# LineworksBot

**LineworksBot for QA**

功能說明:
1. listen聊天室訊息, 並給予合適的反饋或操作
2. 串接Lineworks API, 提供接口透過AWS-QA-小奴才發話



BUILD COMMAND

`docker build -t lineworks .`

`sudo docker run -d --rm --name lineworks --network=my-custom-net -p 9001:9000 lineworks:latest`


