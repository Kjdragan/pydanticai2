Your First API Call
The DeepSeek API uses an API format compatible with OpenAI. By modifying the configuration, you can use the OpenAI SDK or softwares compatible with the OpenAI API to access the DeepSeek API.

PARAM	VALUE
base_url *       	https://api.deepseek.com
api_key	apply for an API key
* To be compatible with OpenAI, you can also use https://api.deepseek.com/v1 as the base_url. But note that the v1 here has NO relationship with the model's version.

* The deepseek-chat model has been upgraded to DeepSeek-V3. The API remains unchanged. You can invoke DeepSeek-V3 by specifying model='deepseek-chat'.

Invoke The Chat API
Once you have obtained an API key, you can access the DeepSeek API using the following example scripts. This is a non-stream example, you can set the stream parameter to true to get stream response.

curl
python
nodejs
# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI

client = OpenAI(api_key="<DeepSeek API Key>", base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)


# context length is 64K tokens so relatively small so will need to keep that in mind regarding batching. Same for output cntext which is 8K



"""Error codes: 

Error Codes
When calling DeepSeek API, you may encounter errors. Here list the causes and solutions.

                    CODE                    	DESCRIPTION
400 - Invalid Format	Cause: Invalid request body format.
Solution: Please modify your request body according to the hints in the error message. For more API format details, please refer to DeepSeek API Docs.
401 - Authentication Fails	Cause: Authentication fails due to the wrong API key.
Solution: Please check your API key. If you don't have one, please create an API key first.
402 - Insufficient Balance	Cause: You have run out of balance.
Solution: Please check your account's balance, and go to the Top up page to add funds.
422 - Invalid Parameters	Cause: Your request contains invalid parameters.
Solution: Please modify your request parameters according to the hints in the error message. For more API format details, please refer to DeepSeek API Docs.
429 - Rate Limit Reached	Cause: You are sending requests too quickly.
Solution: Please pace your requests reasonably. We also advise users to temporarily switch to the APIs of alternative LLM service providers, like OpenAI.
500 - Server Error	Cause: Our server encounters an issue.
Solution: Please retry your request after a brief wait and contact us if the issue persists.
503 - Server Overloaded	Cause: The server is overloaded due to high traffic.
Solution: Please retry your request after a brief wait.
"""