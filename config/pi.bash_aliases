alias cpu="ps -e -o pcpu,pmem,user,pid,state,args --sort -pcpu | sed '/^ 0.0 /d'"
alias sql="mysql -u root -p"
alias sqlc="mysqlcheck -u root -p --auto-repair --optimize --all-databases"
alias update="sudo apt-get -y update && sudo apt-get -y upgrade && sudo apt-get -y dist-upgrade && sudo apt-get -y autoclean && sudo apt-get -y clean && sudo apt-get -y autoremove"
alias omx="omxplayer --blank --vol -900"

