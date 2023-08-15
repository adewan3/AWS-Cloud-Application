echo "Running ServerApp.py"
count=0
while [ $count -le 11 ]
do
cd /home/ubuntu/
python3 serverapp.py
count=$(( $count + 1 ))
sleep 5
done