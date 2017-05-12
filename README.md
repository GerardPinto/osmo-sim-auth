# osmo-sim-auth
This repository contains python script to read SIM card information and also performs GSM/UMTS authentication.
The project is inspired from Osmocom projects: osmo-sim-auth which originally contained GSM/UMTS SIM card authetication parameters.
osmo-sim-auth clonned project: http://osmocom.org/projects/osmo-sim-auth/wiki

Dependencies:
 - Software
	'pcsc_lite' library installed.
 - Hardware
	SIM card reader

Guide to begin:
./osmo-sim-auth --help [To bigin with help commands]
E.g: ./osmo-sim-auth -p IMSI -s (This command will print the IMSI present in th e SIM card)

Contributions:
The project is more complete with read all paramters of the SIM card e.g Kc,ISMI,LOCI etc.
It has been built reading the GSM SIM card specifications and reverse engineering SIM card manager in Layer23 of OsmocomBB application.

Links:
1. osmo-sim-auth (Orginal code): http://osmocom.org/projects/osmo-sim-auth/wiki
2. OsmocomBB: 
3. GSM SIM card specification:

Other SIM card related projects:
1. PySIM: https://github.com/osmocom/pysim
2. SIMtrace


