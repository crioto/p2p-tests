#!/bin/bash

showhelp()
{
cat << ENDHELP

usage: test-p2p [options]
Integration crosspeer test for p2p

Options:
    --remote
        If set - remote peers will be used

    --local 
        If set - local p2p daemon will be started

    --dhcp 
        If set - DHCP option will be used instead of IP (but on first env)
    
    --single
        If set - only single working environment will be created

    --stop
        Kills remote and local p2p daemon

    --file
        Get hosts from file "hosts.list"
    
    --help
        Display this help screen

2018 Subutai [subutai.io]
ENDHELP
}


if which tput >/dev/null 2>&1; then
      ncolors=$(tput colors)
fi
if [ -t 1 ] && [ -n "$ncolors" ] && [ "$ncolors" -ge 8 ]; then
    RED="$(tput setaf 1)"
    GREEN="$(tput setaf 2)"
    YELLOW="$(tput setaf 3)"
    BLUE="$(tput setaf 4)"
    GRAY="$(tput setaf 7)"
    BOLD="$(tput bold)"
    NORMAL="$(tput sgr0)"
else
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    GRAY=""
    BOLD=""
    NORMAL=""
fi

unrecoverable() 
{
    echo ""
    echo "${BOLD}Fatal Error!${NORMAL}"
    exit 1
}

show_fail()
{
    echo -e "\r\t\t\t\t\t\t\t\t\t${RED}${BOLD}[FAIL]${NORMAL}"
}

show_ok()
{
    echo -e "\r\t\t\t\t\t\t\t\t\t${GREEN}${BOLD}[OK]${NORMAL}"
}

show_done()
{
    echo -e "\r\t\t\t\t\t\t\t\t\t${GREEN}${BOLD}[DONE]${NORMAL}"
}


single=0
remote=0
argStop=0
argFile=0
argLocal=0
argDhcp=0
argBuild=0

os=`uname -s`
filename=hosts.list
round=0

original_directory=`pwd`
if [ -L ${BASH_SOURCE[0]} ]; then
    original_directory=`dirname $(readlink ${BASH_SOURCE[0]})`
fi

REMOTE_APP=/tmp/p2p

# Location of p2p sources
SRCDIR=$GOPATH/src/github.com/subutai-io/p2p
DIR=$SRCDIR/bin
# Path to logfile
LOG_PATH=/tmp/p2p-daemon-test.log
# Prefix used in environment name
PREFIX=`date +%Y%m%d%H%M%S`

while [ $# -ge 1 ]; do
    case "$1" in
        --single)
            single=1 ;;
        --remote)
            remote=1 ;;
        --local)
            argLocal=1 ;;
        --dhcp)
            argDhcp=1 ;;
        --build)
            argBuild=1 ;;
        --stop)
            argStop=1 
            ;;
        --file)
            argFile=1 ;;
        --help)
            showhelp
            exit 0
            ;;
        *)
            echo "ERROR: Unknown argument: $1"
            showhelp
            exit 1
            ;;
    esac

    shift
done

# Acquire sudo prvilieges right away
sudo ls / >/dev/null 2>&1

build_p2p()
{
    if [ $argStop -eq 1 ]; then
        return
    fi
    local lpwd=`pwd`
    cd $SRCDIR
    echo -ne "Configuring p2p"
    ./configure > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        show_fail
        unrecoverable
        exit 5
    else
        show_ok
    fi
    echo -ne "Building p2p"
    make clean > /dev/null 2>&1
    make all > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        show_fail
        unrecoverable
        exit 5
    else
        show_ok
    fi
    cd $lpwd
}

stop_remote()
{
    local rhost=$1
    local rport=$2
    local ssh_line="ssh -p${rport} ${rhost}"
    echo -ne "Stopping p2p"
    $ssh_line "killall -9 p2p > /dev/null  2>&1" > /dev/null  2>&1
    $ssh_line "systemctl stop p2p.service > /dev/null  2>&1" > /dev/null  2>&1
    $ssh_line "systemctl stop snap.subutai.p2p-service.service > /dev/null  2>&1" > /dev/null  2>&1
    $ssh_line "systemctl stop snap.subutai-dev.p2p-service.service > /dev/null  2>&1" > /dev/null  2>&1
    $ssh_line "systemctl stop snap.subutai-master.p2p-service.service > /dev/null  2>&1" > /dev/null  2>&1
    $ssh_line "systemctl stop snap.subutai-sysnet.p2p-service.service > /dev/null  2>&1" > /dev/null  2>&1
    show_ok
}

run_remote()
{
    local rhost=$1
    local rport=$2
    local lround=$3
    local amount=5
    local sshcmd="ssh -n "
    echo -ne "Contacting $rhost via $rport"
    $sshcmd -p$rport $rhost "ls -l" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        show_ok
    else
        show_fail
    fi
    stop_remote $rhost $rport
    
    echo -ne "Copying p2p to remote host"
    scp -P$rport $DIR/p2p $rhost:$REMOTE_APP > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        show_ok
    else
        show_fail
    fi

    echo -ne "Starting daemon on remote host"

    $sshcmd -p$rport $rhost "sudo $REMOTE_APP daemon > $LOG_PATH 2>&1 &"
    
    remote_started=0
    for i in {1..10}; do
        sleep 3
        out=`ssh -p$rport $rhost '/tmp/p2p show > /dev/null 2>&1'`
        if [ $? -eq 0 ]; then
            remote_started=1
            show_ok
            break
        fi
    done
    if [ $remote_started -ne 1 ]; then
        show_fail
        unrecoverable
    fi

    $sshcmd -p$rport $rhost "$REMOTE_APP set -log DEBUG > /dev/null 2>&1 &"
    echo -ne "Starting env-${PREFIX}-1 remotely"
    $sshcmd -p$rport $rhost "$REMOTE_APP start -ip 10.100.1.${lround} -hash $PREFIX-working-env-1 -key working-key-1 > /dev/null 2>&1 &"
    if [ $? -eq 0 ]; then
        show_ok
    else
        show_fail
        unrecoverable
    fi

    echo -ne "Running checks"
    show_ok
    return 0
}


stop_test()
{
    local rhost=$1
    local rport=$2
    local lround=$3
    local thispc=$4
    if [ -z "$thispc" ]; then
        local sshcmd="ssh -n -p${rport} ${rhost}"
        echo -ne "Stopping on $rhost via $rport"
    else
        local sshcmd="bash -c "
        echo -ne "Stopping local p2p"
    fi

    $sshcmd "sudo killall -9 p2p > /dev/null 2>&1" > /dev/null 2>&1
    if [ "$os" == "Linux" ]; then
        $sshcmd "sudo killall -9 snap.subutai.p2p-service.service > /dev/null 2>&1" > /dev/null 2>&1
        $sshcmd "sudo killall -9 snap.subutai-master.p2p-service.service > /dev/null 2>&1" > /dev/null 2>&1
        $sshcmd "sudo killall -9 snap.subutai-dev.p2p-service.service > /dev/null 2>&1" > /dev/null 2>&1
        $sshcmd "sudo killall -9 snap.subutai-sysnet.p2p-service.service > /dev/null 2>&1" > /dev/null 2>&1
        $sshcmd "sudo killall -9 p2p.service > /dev/null 2>&1" > /dev/null 2>&1
    else
        $sshcmd "sudo launchctl unload /Library/LaunchDaemons/io.subutai.p2p.daemon.plist > /dev/null 2>&1" > /dev/null 2>&1
    fi

    show_ok
}

run_file()
{
    echo -ne "Checking if ${filename} exists"
    if [ ! -e "$original_directory/$filename" ]; then
        show_fail
        unrecoverable
    else
        show_ok
    fi

    hosts[0]=""
    ports[0]=""
    i=0

    while IFS='' read -r line || [[ -n "$line" ]]; do
        let "i++"
        separator=`printf '%s\n' $line | grep -o . | grep -n ':' | grep -oE '[0-9]+'` 
        h=`echo ${line:0:$separator-1}`
        p=`echo ${line:$separator}`
        hosts[$i]=$h
        ports[$i]=$p
    done < "$original_directory/$filename"    

    n=0
    for var in "${hosts[@]}"
    do
        let "round++"
        let "n++"
        h=${hosts[$n]}
        p=${ports[$n]}
        if [ -z $h ]; then
            continue
        fi

        if [ -z $p ]; then
            continue
        fi

        if [ $argStop -eq 1 ]; then
            stop_remote $h $p $round
        else
            run_remote $h $p $round
        fi
        
        if [ $? -ne 0 ]; then
            show_fail
            unrecoverable
        else
            show_ok
        fi
    done
    
    exit 0
}

stop_local_darwin()
{
    echo -ne "Stopping local p2p"
    sudo launchctl unload /Library/LaunchDaemons/io.subutai.p2p.daemon.plist >/dev/null 2>&1
    sudo killall -9 p2p >/dev/null 2>&1
    show_ok
}

stop_local_linux()
{
    echo -ne "Stopping local p2p"
    sudo
}

run_local()
{
    stop_test "1" "2" "3" "local"

    if [ "$os" == "Darwin" ]; then
        local bin_name=p2p_osx
    else
        local bin_name=p2p
    fi

    echo -ne "Checking P2P build for $os"
    if [ -e $DIR/$bin_name ]; then
        show_ok
    else
        show_fail
        return 1
    fi
    echo -ne "Running daemon"
    sudo $DIR/$bin_name daemon > $LOG_PATH &
    local started=0
    for i in {1..10}; do
        sleep 3
        $DIR/$bin_name show > /dev/null 2>&1
        if [ $? -eq 0 ]; then
            local started=1
            show_ok
            break
        fi
    done
    if [ $started -ne 1 ]; then
        show_fail
        return 2
    fi

    if [ $argDhcp -eq 1 ]; then
        local ipline="dhcp"
    else
        local lround=$round
        let "lround++"
        local ipline="10.100.1.$lround"
    fi
    echo -ne "Starting instance"
    $DIR/$bin_name start --hash $PREFIX-working-env-1 --key working-key-1 --ip $ipline > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        show_fail
    else
        show_ok
    fi
}

if [ $argBuild -eq 1 ]; then
    build_p2p
fi

if [ $argFile -eq 1 ]; then
    run_file
fi

if [ $argLocal -eq 1 ]; then
    run_local
fi