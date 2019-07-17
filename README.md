# slack-sten-bot
Чтобы локально развернуть сервер необходимо установить [ngrok](https://ngrok.com). В папке с ngrok запустить команду:	   
```./ngrok http 5000```     
 Полученный публичный URL указать в ЛК slack (https).  

**Поля в которых нужно заменить URL:** 	
*Interactive Components - Interactivity*    
*Interactive Components - Message Menus*    
*OAuth & Permissions - Redirect URLs*    
*Event Subscriptions - Request URL*    

 Если перезапустить ngrok, URL перегенерируется.
 Чтобы пройти аутентификацию в slack, необходимо запустить проект в другом терминале.    
 ```python3 app.py```   
 или 
  ```docker-compose up ```
