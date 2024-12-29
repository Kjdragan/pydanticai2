# Code execution

The Gemini API code execution feature enables the model to generate and run Python code and learn iteratively from the results until it arrives at a final output. You can use this code execution capability to build applications that benefit from code-based reasoning and that produce text output. For example, you could use code execution in an application that solves equations or processes text.

Code execution is available in both AI Studio and the Gemini API. In AI Studio, you can enable code execution under **Advanced settings**. The Gemini API provides code execution as a tool, similar to [function calling](/gemini-api/docs/function-calling/tutorial). After you add code execution as a tool, the model decides when to use it.

**Note:** The code execution environment includes the [NumPy](https://numpy.org/) and [SymPy](https://www.sympy.org/en/index.html) libraries. You can't install your own libraries.

## Get started with code execution

A code execution notebook is also available:

[![](https://ai.google.dev/static/site-assets/images/docs/notebook-site-button.png)View on ai.google.dev](https://ai.google.dev/gemini-api/docs/code-execution) |  [![](https://www.tensorflow.org/images/colab_logo_32px.png)Try a Colab notebook](https://colab.research.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Code_Execution.ipynb) |  [![](https://www.tensorflow.org/images/GitHub-Mark-32px.png)View notebook on GitHub](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Code_Execution.ipynb)  
---|---|---  

This section assumes that you've completed the setup and configuration steps shown in the [quickstart](/gemini-api/docs/quickstart).

### Enable code execution on the model

You can enable code execution on the model, as shown here:

```python
import os
import google.generativeai as genai

genai.configure(api_key=os.environ['API_KEY'])
model = genai.GenerativeModel(
  model_name='gemini-1.5-pro',
  tools='code_execution')
response = model.generate_content((
  'What is the sum of the first 50 prime numbers? '
  'Generate and run code for the calculation, and make sure you get all 50.'))
print(response.text)
```

The output might look something like this:

```python
def is_prime(n):
 """Checks if a number is prime."""
 if n <= 1:
  return False
 for i in range(2, int(n**0.5) + 1):
  if n % i == 0:
   return False
 return True

def sum_of_primes(n):
 """Calculates the sum of the first n prime numbers."""
 primes = []
 i = 2
 while len(primes) < n:
  if is_prime(i):
   primes.append(i)
  i += 1
 return sum(primes)

# Calculate the sum of the first 50 prime numbers
sum_of_first_50_primes = sum_of_primes(50)
print(f"The sum of the first 50 prime numbers is: {sum_of_first_50_primes}")
```

**Explanation:**
1. **`is_prime(n)` Function:**
  - Takes an integer `n` as input.
  - Returns `False` for numbers less than or equal to 1 (not prime).
  - Iterates from 2 up to the square root of `n`. If `n` is divisible by any number in this range, it's not prime, and we return `False`.
  - If the loop completes without finding a divisor, the number is prime, and we return `True`.
2. **`sum_of_primes(n)` Function:**
  - Takes an integer `n` (number of primes desired) as input.
  - Initializes an empty list `primes` to store the prime numbers.
  - Starts a loop, iterating through numbers starting from 2.
  - For each number `i`, it checks if it's prime using the `is_prime()` function.
  - If `i` is prime, it's appended to the `primes` list.
  - The loop continues until the `primes` list has `n` prime numbers.
  - Finally, it calculates and returns the sum of all the prime numbers in the `primes` list.
3. **Main Part:**
  - Calls `sum_of_primes(50)` to get the sum of the first 50 prime numbers.
  - Prints the result.
**Output:**
```
The sum of the first 50 prime numbers is: 5117
```

### Enable code execution on the request

Alternatively, you can enable code execution on the call to `generate_content`:

```python
import os
import google.generativeai as genai

genai.configure(api_key=os.environ['API_KEY'])
model = genai.GenerativeModel(model_name='gemini-1.5-pro')
response = model.generate_content(
  ('What is the sum of the first 50 prime numbers? '
  'Generate and run code for the calculation, and make sure you get all 50.'),
  tools='code_execution')
print(response.text)
```

### Use code execution in chat

You can also use code execution as part of a chat.

```python
import os
import google.generativeai as genai

genai.configure(api_key=os.environ['API_KEY'])
model = genai.GenerativeModel(model_name='gemini-1.5-pro',
               tools='code_execution')
chat = model.start_chat()
response = chat.send_message((
  'What is the sum of the first 50 prime numbers? '
  'Generate and run code for the calculation, and make sure you get all 50.'))
print(response.text)
```

## Code execution versus function calling

Code execution and [function calling](/gemini-api/docs/function-calling) are similar features:

  * Code execution lets the model run code in the API backend in a fixed, isolated environment.
  * Function calling lets you run the functions that the model requests, in whatever environment you want.

In general you should prefer to use code execution if it can handle your use case. Code execution is simpler to use (you just enable it) and resolves in a single `GenerateContent` request (thus incurring a single charge). Function calling takes an additional `GenerateContent` request to send back the output from each function call (thus incurring multiple charges).

For most cases, you should use function calling if you have your own functions that you want to run locally, and you should use code execution if you'd like the API to write and run Python code for you and return the result.

## Billing

There's no additional charge for enabling code execution from the Gemini API. You'll be billed at the current rate of input and output [tokens](/gemini-api/docs/tokens).

Here are a few other things to know about billing for code execution:

  * You're only billed once for the input tokens you pass to the model, and you're billed for the final output tokens returned to you by the model.
  * Tokens representing generated code are counted as output tokens.
  * Code execution results are also counted as output tokens.

## Limitations

  * The model can only generate and execute code. It can't return other artifacts like media files.
  * The feature doesn't support file I/O or use cases that involve non-text output (for example, data plots or a CSV file upload).
  * Code execution can run for a maximum of 30 seconds before timing out.
  * In some cases, enabling code execution can lead to regressions in other areas of model output (for example, writing a story).
  * There is some variation in the ability of the different models to use code execution successfully. Gemini 1.5 Pro is the best performing model, based on our testing.