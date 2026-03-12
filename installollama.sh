@/bin/bash
echo ARE YOU IN THE DIRECTORY OF THE SCRIPT? IF NOT, CD INTO THTA DIRECTORY, THEN RUN THE SCRIPT!
read -p "Press [Enter] key to continue..."   
echo Installing ollama... YOU WILL BE PROMPTED FOR A PASSWORD!
curl -fsSL https://ollama.com/install.sh | sh
echo Please sign in with a ollama account...
ollama signin
echo Downloading models...
ollama pull qwen3-next:80b-cloud
ollama pull gpt-oss:120b-cloud
echo Installing python and pip... YOU WILL BE PROMPTED FOR A PASSWORD!
sudo apt update
sudo apt install -y python3 
sudo apt install -y python3-pip
echo Installing packages...
pip3 install -r req.txt

echo You are now ready to run the program!