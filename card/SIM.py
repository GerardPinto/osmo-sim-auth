"""
card: Library adapted to request (U)SIM cards and other types of telco cards.
Copyright (C) 2010 Benoit Michau

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

#################################
# Python library to work on
# SIM card
# communication based on ISO7816 card
#
# needs pyscard from:
# http://pyscard.sourceforge.net/
#################################

from binascii import *
from card.ICC import ISO7816
from card.FS import SIM_FS
from card.utils import *
from time import sleep


class SIM(ISO7816):
    '''
    define attributes, methods and facilities for ETSI / 3GPP SIM card
    check SIM specifications in ETSI TS 102.221 and 3GPP TS 51.011
    
    inherit methods and objects from ISO7816 class
    use self.dbg = 1 or more to print live debugging information
    '''

    caller = None
    
    def __init__(self):
        '''
        initialize like an ISO7816-4 card with CLA=0xA0
        can also be used for USIM working in SIM mode,
        '''
        ISO7816.__init__(self, CLA=0xA0)
        if self.dbg:
            print '[DBG] type definition: %s' % type(self)
            print '[DBG] CLA definition: %s' % hex(self.CLA)

        self.caller = {
        'Kc' : self.get_Kc,
        'IMSI' : self.get_imsi,
        'LOCI' : self.get_loci,
        'HPLMN' : self.get_subscr_sim_hplmn,
        'PLMN_SEL' : self.get_subscr_sim_plmnsel,
        'ICCID' : self.get_subscr_iccid,
        'SPN' : self.get_subscr_sim_spn,
        'ACC' : self.get_subscr_sim_acc,
        'FPLMN' : self.get_subscr_sim_fplmn,
        'MSISDN' : self.get_subscr_sim_msisdn,
        'PRINT_ALL' : self.print_sim_card_info,
        'Kc-W' : self.write_subscr_Kc,
        'LOCI-W' : self.write_subscr_loci,
        'SMSP' : self.get_subscr_smsp,
        'GSM_ALGO' : self.run_gsm_algorithm
        }
        
    
    def sw_status(self, sw1, sw2):
        '''
        sw_status(sw1=int, sw2=int) -> string
        
        extends SW status bytes interpretation from ISO7816 
        with ETSI / 3GPP SW codes
        helps to speak with the smartcard!
        '''
        status = ISO7816.sw_status(self, sw1, sw2)
        if sw1 == 0x91: status = 'normal processing, with extra info ' \
            'containing a command for the terminal: length of the ' \
            'response data %d' % sw2
        elif sw1 == 0x9E: status = 'normal processing, SIM data download ' \
            'error: length of the response data %d' % sw2
        elif sw1 == 0x9F: status = 'normal processing: length of the ' \
            'response data %d' % sw2
        elif (sw1, sw2) == (0x93, 0x00): status = 'SIM application toolkit ' \
            'busy, command cannot be executed at present'
        elif sw1 == 0x92 :
            status = 'memory management'
            if sw2 < 16: status += ': command successful but after %d '\
                'retry routine' % sw2
            elif sw2 == 0x40: status += ': memory problem'
        elif sw1 == 0x94:
            status = 'referencing management'
            if sw2 == 0x00: status += ': no EF selected'
            elif sw2 == 0x02: status += ': out of range (invalid address)'
            elif sw2 == 0x04: status += ': file ID or pattern not found'
            elif sw2 == 0x08: status += ': file inconsistent with the command'
        elif sw1 == 0x98:
            status = 'security management'
            if sw2 == 0x02: status += ': no CHV initialized'
            elif sw2 == 0x04: status += ': access condition not fulfilled, ' \
                'at least 1 attempt left'
            elif sw2 == 0x08: status += ': in contradiction with CHV status'
            elif sw2 == 0x10: status += ': in contradiction with ' \
                'invalidation status'
            elif sw2 == 0x40: status += ': unsuccessful CHV verification, ' \
                'no attempt left'
            elif sw2 == 0x50: status += ': increase cannot be performed, ' \
                'max value reached'
            elif sw2 == 0x62: status += ': authentication error, ' \
                'application specific'
            elif sw2 == 0x63: status += ': security session expired'
        return status
    
    def verify_pin(self, pin='', pin_type=1):
        '''
        verify CHV1 (PIN code) or CHV2 with VERIFY APDU command
        call ISO7816 VERIFY method
        '''
        if pin_type in [1, 2] and type(pin) is str and \
        len(pin) == 4 and 0 <= int(pin) < 10000:
            PIN = [ord(i) for i in pin] + [0xFF, 0xFF, 0xFF, 0xFF]
            self.coms.push( self.VERIFY(P2=pin_type, Data=PIN) )
        else: 
            if self.dbg: 
                print '[WNG] bad parameters'
    
    def disable_pin(self, pin='', pin_type=1):
        '''
        disable CHV1 (PIN code) or CHV2 with DISABLE_CHV APDU command
        TIP: do it as soon as you can when you are working 
        with a SIM / USIM card for which you know the PIN!
        call ISO7816 DISABLE method
        '''
        if pin_type in [1, 2] and type(pin) is str and \
        len(pin) == 4 and 0 <= int(pin) < 10000:
            PIN = [ord(i) for i in pin] + [0xFF, 0xFF, 0xFF, 0xFF]
            self.coms.push( self.DISABLE_CHV(P2=pin_type, Data=PIN) )
        else:
            if self.dbg: 
                print '[WNG] bad parameters'
    
    def unblock_pin(self, pin_type=1, unblock_pin=''):
        '''
        WARNING: not correctly implemented!!!
            and PUK are in general 8 nums...
        TODO: make it correctly!

        unblock CHV1 (PIN code) or CHV2 with UNBLOCK_CHV APDU command 
        and set 0000 value for new PIN
        call ISO7816 UNBLOCK_CHV method
        '''
        print 'not correctly implemented'
        return
        #if pin_type == 1: 
        #    pin_type = 0
        if pin_type in [0, 2] and type(unblock_pin) is str and \
        len(unblock_pin) == 4 and 0 <= int(unblock_pin) < 10000:
            UNBL_PIN = [ord(i) for i in unblock_pin] + [0xFF, 0xFF, 0xFF, 0xFF]
            self.coms.push( self.UNBLOCK_CHV(P2=pin_type, Lc=0x10, \
                            Data=UNBL_PIN + \
                            [0x30, 0x30, 0x30, 0x30, 0xFF, 0xFF, 0xFF, 0xFF]) )
        else:
            if self.dbg: 
                print '[WNG] bad parameters'
            #return self.UNBLOCK_CHV(P2=pin_type)
    
    def parse_file(self, Data=[]):
        '''
        parse_file(Data=[0x12, 0x34, 0x56, 0x89]) -> dict(file)
        
        parses a list of bytes returned when selecting a file
        interprets the content of some informative bytes for right accesses, 
        type / format of file... see TS 51.011
        works over the SIM file structure
        '''
        fil = {}
        fil['Size'] = Data[2]*0x100 + Data[3]
        fil['File Identifier'] = Data[4:6]
        fil['Type'] = ('RFU', 'MF', 'DF', '', 'EF')[Data[6]]
        fil['Length'] = Data[12]
        if fil['Type'] == 'MF' or fil['Type'] == 'DF':
            fil['DF_num'] = Data[14]
            fil['EF_num'] = Data[15]
            fil['codes_num'] = Data[16]
            fil['CHV1'] = ('not initialized','initialized')\
                          [(Data[18] & 0x80) / 0x80]\
                        + ': %d attempts remain' % (Data[18] & 0x0F)
            fil['unblock_CHV1'] = ('not initialized','initialized')\
                                  [(Data[19] & 0x80) / 0x80]\
                                + ': %d attempts remain' % (Data[19] & 0x0F)
            fil['CHV2'] = ('not initialized','initialized')\
                          [(Data[20] & 0x80) / 0x80]\
                        + ': %d attempts remain' % (Data[20] & 0x0F)
            fil['unblock_CHV2'] = ('not initialized','initialized')\
                                  [(Data[21] & 0x80) / 0x80]\
                                + ': %d attempts remain' % (Data[21] & 0x0F)
            if len(Data) > 23: 
                fil['Adm'] = Data[23:]
        elif fil['Type'] == 'EF':
            cond = ('ALW', 'CHV1', 'CHV2', 'RFU', 'ADM_4', 'ADM_5', 
                    'ADM_6', 'ADM_7', 'ADM_8', 'ADM_9', 'ADM_A',
                    'ADM_B', 'ADM_C', 'ADM_D', 'ADM_E', 'NEW')
            fil['UPDATE'] = cond[Data[8] & 0x0F]
            fil['READ'] = cond[Data[8] >> 4]
            fil['INCREASE'] = cond[Data[9] >> 4]
            fil['INVALIDATE'] = cond[Data[10] & 0x0F]
            fil['REHABILITATE'] = cond[Data[10] >> 4]
            fil['Status'] = ('not read/updatable when invalidated', 
                              'read/updatable when invalidated')\
                            [byteToBit(Data[11])[5]] \
                          + (': invalidated',': not invalidated')\
                            [byteToBit(Data[11])[7]]
            fil['Structure'] = ('transparent', 'linear fixed', '', 'cyclic')\
                               [Data[13]]
            if fil['Structure'] == 'cyclic': 
                fil['INCREASE'] = byteToBit(Data[7])[1]
            if len(Data) > 14: 
                fil['Record Length'] = Data[14]
        return fil
    
    def run_gsm_alg(self, RAND=16*[0x00]):
        '''
        self.run_gsm_alg( RAND ) -> ( SRES, Kc )
            RAND : list of bytes, length 16
            SRES : list of bytes, length 4
            Kc : list of bytes, length 8
            
        run GSM authentication algorithm: 
            accepts any kind of RAND (old GSM fashion)
        feed with RAND 16 bytes value
        return a list with SRES and Kc, or None on error
        '''
        if len(RAND) != 16:
            if self.dbg: 
                print '[WNG] needs a 16 bytes input RAND value'
            return None
        # select DF_GSM directory
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        # run authentication
        self.coms.push(self.INTERNAL_AUTHENTICATE(P1=0x00, P2=0x00, Data=RAND))
        if self.coms()[2][0] != 0x9F:
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        # get authentication response
        self.coms.push(self.GET_RESPONSE(Le=self.coms()[2][1]))
        if self.coms()[2] != (0x90, 0x00):
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        SRES, Kc = self.coms()[3][0:4], self.coms()[3][4:]
        return [ SRES, Kc ]
    
    def get_imsi(self):
        '''
        self.get_imsi() -> string(IMSI)
        
        reads IMSI value at address [0x6F, 0x07]
        returns IMSI string on success or None on error
        '''
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select IMSI file
        imsi = self.select([0x6F, 0x07])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # and parse the received data into the IMSI structure
        if 'Data' in imsi.keys() and len(imsi['Data']) == 9:
            return imsi['Data']
        
        # if issue with the content of the DF_IMSI file
        if self.dbg: 
            print '[DBG] %s' % self.coms()
        return None

    def get_Kc(self):
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select Kc file
        Kc = self.select([0x6F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
            
        if 'Data' in Kc.keys() and len(Kc['Data']) == 9:
            return Kc['Data']
        return None

    def get_loci(self):
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select TMSI, MCC, MNC, LAC from file which is 11 bytes = loci
        loci = self.select([0x6F, 0x7E])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        if 'Data' in loci.keys() and len(loci['Data']) == 11:
            return loci['Data']            
        else:
            return None

    def get_subscr_sim_plmnsel(self):
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        plmnsel = self.select([0x6F, 0x30])      
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        if 'Data' in plmnsel.keys():
            return plmnsel['Data']
        else:
            return None    

    def get_subscr_sim_hplmn(self):
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select hplmn = 1 byte
        hplmn = self.select([0x6F, 0x31])     
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        if 'Data' in hplmn.keys() and len(hplmn['Data']) == 1:
            return hplmn['Data']
        else:
            return None

    def get_subscr_iccid(self):
        self.select([0x3F, 0x00])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        # select iccid = 10 bytes
        iccid = self.select([0x2F, 0xE2])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        if 'Data' in iccid.keys() and len(iccid['Data']) == 10:
            return iccid['Data']
        else:
            return None

    def get_subscr_sim_spn(self):
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select spn = 17 bytes 0x6f46
        spn = self.select([0x6F, 0x46])
        if spn == None: 
            return []

        if 'Data' in spn.keys() and len(spn['Data']) == 17:
            return spn['Data']
        else:
            return []

    def get_subscr_sim_acc(self):
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select acc = 17 bytes 0x6f78 2 bytes
        acc = self.select([0x6F, 0x78])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        if 'Data' in acc.keys() and len(acc['Data']) == 2:
            return acc['Data']
        else:
            return None

    def get_subscr_sim_fplmn(self):
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select fplmn = 17 bytes 0x6f7b 2 bytes
        fplmn = self.select([0x6F, 0x7b])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        if 'Data' in fplmn.keys() and len(fplmn['Data']) == 12:
            return fplmn['Data']
        else:
            return None

    def get_subscr_sim_msisdn(self):
        # select DF_TELECOM for SIM card = 0x7f10
        self.select([0x7F, 0x10])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select msisdn = 17 bytes 0x6f40 2 bytes
        msisdn = self.select([0x6F, 0x40])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        if 'Data' in msisdn.keys():
            return msisdn['Data'][0]
        else:
            return None

    def get_subscr_smsp(self):
        # select DF_TELECOM for SIM card = 0x7f10
        self.select([0x7F, 0x10])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # select smsp = 0x6f42 = (28 + n) bytes n+14 to n+24 = 12 bytes
        smsp = self.select([0x6F, 0x42])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None        

        if 'Data' in smsp.keys() and len(smsp['Data'][0]) == 44:
            return smsp['Data'][0]
        else:
            return None

    def run_gsm_algorithm(self, RAND):
        print RAND
        print "We are going to wait for 2 seconds===================="
        sleep(2)
        print "Done waiting========================================"
        response = self.run_gsm_alg(stringToByte(a2b_hex(RAND)))
        SRES = response[0]
        Kc = response[1]
        print Kc
        Kc.append(0)
        print Kc
        print b2a_hex(byteToString(Kc))
        ALGO_RESP = SRES + Kc
        print ALGO_RESP
        return ALGO_RESP

    def write_subscr_Kc(self, Data):
        Data =  stringToByte(a2b_hex(Data))
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        # select Kc to write
        self.select([0x6F, 0x20])        
        if self.coms()[2] != (0x90, 0x00):
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # update Kc
        self.update([0x6F, 0x20], Data)
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        return self.get_Kc()

    def write_subscr_loci(self, Data):
        Data = stringToByte(a2b_hex(Data))
        # select DF_GSM for SIM card
        self.select([0x7F, 0x20])
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        # select TMSI, MCC, MNC, LAC from file which is 11 bytes = loci to write
        self.select([0x6F, 0x7E])        
        if self.coms()[2] != (0x90, 0x00):
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None
        
        # update TMSI, MCC, MNC, LAC from file which is 11 bytes = loci
        self.update([0x6F, 0x7E], Data)
        if self.coms()[2] != (0x90, 0x00): 
            if self.dbg: 
                print '[DBG] %s' % self.coms()
            return None

        return self.get_loci()


    def print_sim_card_info(self):
        Kc = self.get_Kc()
        print Kc
        print "Stored Kc:\t\t\t\t%s\n" % b2a_hex(byteToString(Kc))   

        loci = self.get_loci()
        print loci
        TMSI, LAI, TMSI_TIME, LOC_UPDATE_STATUS = loci[0:4], loci[4:9], loci[9], loci[10]        
        print "Stored TMSI:\t\t\t\t%s \n" % b2a_hex(byteToString(TMSI))
        MCC = ((LAI[0] & 0x0f) << 8) | (LAI[0] & 0xf0) | (LAI[1] & 0x0f)
        MNC = ((LAI[2] & 0x0f) << 8) | (LAI[2] & 0xf0) | ((LAI[1] & 0xf0) >> 4)
        LAC = LAI[3:5]
        print "Stored LAI (MCC, MNC, LAC):\t\t(%s, %s, %s) \n" % (format(int(hex(MCC),16),"x"), format(int(hex(MNC),16),"x"), b2a_hex(byteToString(LAC)))
        print "Stored TMSI time:\t\t\t%s\n" % b2a_hex(byteToString([TMSI_TIME]))
        print "Location Update Status:\t\t\t%s\n" % b2a_hex(byteToString([LOC_UPDATE_STATUS]))

        imsi = self.get_imsi()
        print imsi
        print "Stored IMSI:\t\t\t\t%s\n" % decode_BCD(imsi)[3:]

        hplmn = self.get_subscr_sim_hplmn()
        print hplmn
        print "Stored HPLMN time interval:\t\t%s\n" %hplmn[0]

        plmnsel = self.get_subscr_sim_plmnsel()
        print plmnsel
        print "Stored PLMN selector:\t\t\tMCC | MNC\n"
        index = 0
        while len(plmnsel) > 3 and index < len(plmnsel):
            if plmnsel[index] == 0xFF and plmnsel[index+1] == 0xFF and plmnsel[index+2] == 0xFF:
                break
            else:
                MCC = ((plmnsel[index] & 0x0f) << 8) | (plmnsel[index] & 0xf0) | (plmnsel[index+1] & 0x0f)
                MNC = ((plmnsel[index+2] & 0x0f) << 8) | (plmnsel[index+2] & 0xf0) | ((plmnsel[index+1] & 0xf0) >> 4)
                if (MNC & 0x000f) == 0x000f:
                    MNC = MNC >> 4
                    print "\t\t\t\t\t%03x   %02x" %(MCC, MNC)
                else:                   
                    print "\t\t\t\t\t%03x   %03x" %(MCC, MNC)
                index +=3

        iccid = self.get_subscr_iccid()
        print iccid
        print "\nICCID:\t\t\t\t\t%s\n" % decode_BCD(iccid)[:-2]

        spn = self.get_subscr_sim_spn()
        print spn
        print "Service Provide Name:\t\t %s\n" %b2a_hex(byteToString(spn))

        acc = self.get_subscr_sim_acc()
        print acc
        print "ACC:\t\t\t\t\t%s\n" %b2a_hex(byteToString(acc))

        fplmn = self.get_subscr_sim_fplmn()
        print fplmn
        fplmn_str = b2a_hex(byteToString(fplmn))
        fplmn_str = ' '.join(fplmn_str[i:i+6] for i in xrange(0,len(fplmn_str),6))
        print "Forbidden PLMN (FFFFFF => not used):\t%s\n" %fplmn_str

        smsp = self.get_subscr_smsp()
        print smsp
        length = len(smsp) - 28
        start = length + 15
        end = start + 6
        smsp_str = decode_BCD(smsp[start:end])[:-2]
        print "SMSP: \t\t\t\t\t+%s\n" %smsp_str

        msisdn = self.get_subscr_sim_msisdn()
        name_len = len(msisdn) - 14
        print "MSISDN phone number \t\t\t+%s\n" % decode_BCD(msisdn[name_len+2:name_len+8])[:-2]


        print "Running GSM Algorithm:"
        RAND=16*[0x00]
        gsm_algo_response = self.run_gsm_alg(RAND=RAND)        
        print RAND
        print gsm_algo_response[0]
        print gsm_algo_response[1]
        print "RANDOM:\t\t\t\t\t00000000000000000000000000000000"
        print "SRES:\t\t\t\t\t%s" % b2a_hex(byteToString(gsm_algo_response[0]))
        print "Kc (new):\t\t\t\t%s" % b2a_hex(byteToString(gsm_algo_response[1]))