#!/bin/bash
#
# trainidUSB function
# Interpeter the Timing information received via the 115KBaud protocol
# author: Bruno Fernandes (bruno.fernandes@xfel.eu)

function trainidUSB(){    
    local rawMode="" 
    local timeMode=""
    local oneLine=""
    local checkCRC=""
    local checkBeamMode=""
    local testMode="" ; # input is text file (first argument), ETX_dec is standard new line
    local STX_dec='02'
    local ETX_dec='03'
    # check arguments
    local OPTIND; # bash does not reset this variable
    while getopts "rs:e:tocTbh" opt; do
    	case $opt in	    
    	    r) rawMode="on";;
    	    s) STX_dec="${OPTARG#0x}";;
    	    e) ETX_dec="${OPTARG#0x}";;
    	    t) timeMode="on";;
	    o) oneLine="on";;
	    c) checkCRC="on";;
	    b) checkBeamMode="on";;
	    T) ETX_dec='12';testMode="on";;
	    h)
		echo "trainidUSB"
		echo "This functions interprets the information received via the 115KBaud protocol"
		echo "Information has the following format: <STX><Data payload><8bit CRC><ETX>"
		echo "-------------------"
		echo "syntax: trainidUSB [-rtocbTh] [-s stx] [-e etx] [device]"
		echo "Key:"
		echo -e "\t-r"
		echo -e "\t\traw mode: show information as received by the interface (no STX and ETX)"
		echo -e "\t-t"
		echo -e "\t\tdisplay time at which information was received"
		echo -e "\t-o"
		echo -e "\t\toneline mode: overwrite output every time new information is received"
		echo -e "\t-c"
		echo -e "\t\tcalculate CRC data payload and check if matches"
		echo -e "\t-b"
		echo -e "\t\tinterpret beam mode data (not compatible with -o and -r)"
		echo -e "\t-T"
		echo -e "\t\ttest mode: device is a file in the system, each line has data payload and crc data as if received from timing system"
		echo -e "\t-s stx"
		echo -e "\t\tupdate value used for STX. Variable stx should be ASCII decimal value"
		echo -e "\t-e etx"
		echo -e "\t\tupdate value used for ETX. Variable etx should be ASCII decimal value"
		echo -e "\t-h"
		echo -e "\t\tdisplay this menu"
		echo -e "\tdevice"
		echo -e "\t\tif not provided, default is /dev/ttyUSB0"		
		return 0;;
    	    \? ) echo "Option not recognized. Exiting..."
    		 return 1
    	esac
    done
    # Remove arguments given
    shift "$(($OPTIND-1))"
    # Function to convert hexadecimal values (as received in the serial port) in decimal
    function hex2dec(){ echo $((0x$1)) ;}   
    
    local STX_char=`printf "\x$(printf %x $STX_dec)"`
    local ETX_char=`printf "\x$(printf %x $ETX_dec)"`
    local DEVICE=${1:-'/dev/ttyUSB0'}

    # Double check that one line and raw mode is not enable with beam mode
    ! [ -z $checkBeamMode ] && oneLine="" && rawMode="" 
    
    # Check if Device exits and define read argument
    local readArgs=""
    if ! [ -z $testMode ]; then
	! [ -f "$DEVICE" ] && echo "TEST MODE: file $DEVICE is not available in the system! Exiting..." && return 1
    else
	! [ -c "$DEVICE" ] && echo "Device $DEVICE is not available in the system! Exiting..." && return 1
	# Reset any previous configuration in serial port
	stty -F $DEVICE sane   
	# Configure serial port for TrainID USB stick
	# Baud 115220
	# Interrupt signal should be generate with CHAR STX 
	stty -F $DEVICE 115200 intr $STX_dec
	# Reading of line stops at ETX_char
	readArgs="-d $ETX_char"
    fi
         
    # Do until said to stop
    while read $readArgs timingInfo_hex; do
    #while read -d $'\012' timingInfo_hex; do
    #while read timingInfo_hex; do
	local outputLine=""
	! [ -z $oneLine ] && outputLine="\r"
	! [ -z $timeMode ] && outputLine=${outputLine}"At `date +"%T.%6N"` : "
	if ! [ -z $rawMode ] ; then
	    outputLine=${outputLine}"$timingInfo_hex"
	else
	    # Separate first, then convert. String is to long to be directly converted to decimal
	    timingInfoData=${timingInfo_hex:0:24}
	    timingInfoCRC=$(hex2dec ${timingInfo_hex:24})
	
	    trainID=$(hex2dec ${timingInfo_hex:0:16})
	    beamMode_hex=${timingInfo_hex:16:8}
	    beamMode=$(hex2dec $beamMode_hex)
	    local crc=""
	    # Check CRC
	    if ! [ -z $checkCRC ]; then
	    	#CRC calculation
	    	crc=0
	    	for ((i=0; i<${#timingInfoData}/2; i++))
	    	do
	    	    crc=$(($crc ^ $(hex2dec ${timingInfoData:0:2})))
	    	    timingInfoData=${timingInfoData:2}
	    	done
	    	crc=`[ $timingInfoCRC == $crc ] && echo "" || echo "Problem! Calculated CRC: $crc"`
	    fi
	    outputLine=${outputLine}`printf "Train ID: %10d Beam Mode: %8x CRC: %2x %s" $trainID $beamMode $timingInfoCRC "$crc"`
	fi
	echo -ne "$outputLine" 
	[ -z $oneLine ] && echo ""
	if ! [ -z $checkBeamMode ]; then
	    local beamLocations=( "Injector1" "Injector2" "Acc_L1-L3" "TLD" "SASE1/3" "SASE2" )
	    local beamModeInfo=( "[0] No Bunches allowed" "[F]ull Mode (No restrictions)" "[M]edium Mode (<= 300/500 Bunches)" "[S]hort mode (<= 30 Bunches)" "[1] Single Bunch Operation"  )
	    for ((location=0; location<${#beamLocations[@]}; location++))	    
	    do
		# Get beamMode for location in binary
		local localBeamMode=$(echo "ibase=16; obase=2; ${beamMode_hex:$location:1}" | bc)
		# Pad binary value with 0 (otherwise we can't get the right index) and revert bits (since expr index returns the first match and LSB = Full)
		localBeamMode=`printf "%4s" $localBeamMode | tr ' ' '0' | rev`
		# Get index from beamMode where the first '1' occurs
		local localIndex=`expr index $localBeamMode 1`
		printf "%10s : %s\n" "${beamLocations[$location]}" "${beamModeInfo[$localIndex]}"
	    done
	    echo "------------------------"
	fi
    done < $DEVICE
    echo ""
}

	




