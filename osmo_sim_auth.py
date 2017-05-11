#!/usr/bin/python

"""
Test script for (U)SIM authentication
Copyright (C) 2011 Harald Welte <laforge@gnumonks.org>

based heavily on the "card" library by Benoit Michau and pyscard

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

from binascii import *
from card.utils import *
from optparse import OptionParser
from card.USIM import USIM
from card.SIM import SIM
import sys

def handle_usim(options, rand_bin, autn_bin):
	u = USIM()
	if not u:
		print "Error opening USIM"
		exit(1)

	if options.debug:
		u.dbg = 2;

	imsi = u.get_imsi()
	print "Testing USIM card with IMSI %s" % imsi

	print "\nUMTS Authentication"
	ret = u.authenticate(rand_bin, autn_bin, ctx='3G')
	if len(ret) == 1:
		print "AUTS:\t%s" % b2a_hex(byteToString(ret[0]))
	else:
		print "RES:\t%s" % b2a_hex(byteToString(ret[0]))
		print "CK:\t%s" % b2a_hex(byteToString(ret[1]))
		print "IK:\t%s" % b2a_hex(byteToString(ret[2]))
		if len(ret) == 4:
			print "Kc:\t%s" % b2a_hex(byteToString(ret[3]))

	print "\nGSM Authentication"
	ret = u.authenticate(rand_bin, autn_bin, ctx='2G')
	if not len(ret) == 2:
		print "Error during 2G authentication"
		exit(1)
	print "SRES:\t%s" % b2a_hex(byteToString(ret[0]))
	print "Kc:\t%s" % b2a_hex(byteToString(ret[1]))

def handle_sim(options, rand_bin):
	s= SIM()
	if not s:
		print "Error opening SIM"
		exit(1)

	imsi = s.get_imsi()
	ret = s.run_gsm_alg(rand_bin)

	if not options.ipsec:
		print "Testing SIM card with IMSI %s" % imsi
		print "\nGSM Authentication"
		print "SRES:\t%s" % b2a_hex(byteToString(ret[0]))
		print "Kc:\t%s" % b2a_hex(byteToString(ret[1]))

	if options.ipsec:
		print "1%s@uma.mnc%s.mcc%s.3gppnetwork.org,%s,%s,%s" % (imsi, imsi[3:6], imsi[0:3], b2a_hex(byteToString(rand_bin)), b2a_hex(byteToString(ret[0])), b2a_hex(byteToString(ret[1])))

def handle_siminfo(options):
	s= SIM()
	if not s:
		print "Error opening SIM"
		exit(1)

	if options.write is not None:
		return s.caller.get(options.param)(options.write)
	elif options.rand is not None:
		return s.caller.get(options.param)(options.rand)
	else:
		return s.caller.get(options.param)()

def options(parser):
	parser.add_option("-a", "--autn", dest="autn",
			  help="AUTN parameter from AuC - 32 hex digits")
	parser.add_option("-r", "--rand", dest="rand",
			  help="RAND parameter from AuC - 32 hex digits")
	parser.add_option("-d", "--debug", dest="debug",
			  help="Enable debug output",
			  action="store_true")
	parser.add_option("-s", "--sim", dest="sim",
			  help="SIM mode (default: USIM)",
			  action="store_true", default=False)
	parser.add_option("-I", "--ipsec", dest="ipsec",
			  help="IPSEC mode for strongswan triplets.dat",
			  action="store_true")

	parser.add_option("-p", "--param", dest="param",
			  help="Kc|IMSI|LOCI|HPLMN|PLMN_SEL|ICCID|SPN|ACC|FPLMN|MSISDN|SMSP|PRINT_ALL|GSM_ALGO")
	parser.add_option("-w", "--write", dest="write", help="SIM in write mode")

def execute_options():
	parser = OptionParser()
	options(parser)
	(opt, args) = parser.parse_args()

	if opt.param is not None and opt.sim is True:
		output = handle_siminfo(opt)
		if output is not None:
			print output
			print b2a_hex(byteToString(output))
		return output
	elif opt.write is not None and opt.param in ['Kc','LOCI']:
		opt.param = opt.param + '-W'
		return handle_siminfo(opt)
	elif opt.param is not None and opt.rand is not None:
		return handle_siminfo(opt)
	else:
		exit(2)
		if not opt.rand:
			print "You have to specify RAND"
			exit(2)

		rand_bin = stringToByte(a2b_hex(opt.rand))
		if opt.autn:
			autn_bin = stringToByte(a2b_hex(opt.autn))

		if opt.sim == True:
			handle_sim(opt, rand_bin)
		else:
			if not opt.autn:
				print "You have to specify AUTN"
				exit(2)
			handle_usim(opt, rand_bin, autn_bin)

def execute(args):
	args = args.split()
	sys.argv = [sys.argv[0]] + args
	return execute_options()


if __name__ == "__main__":
	execute_options()
