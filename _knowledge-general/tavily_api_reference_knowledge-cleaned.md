## API Reference

### Client

The `TavilyClient` class is the entry point to interacting with the Tavily API. Kickstart your journey by instantiating it with your API key. Once you do so, you're ready to search the Web in one line of code! All you need is to pass a `str` as a `query` to one of our methods (detailed below) and you'll start searching!

### Asynchronous Client

If you want to use Tavily asynchronously, you will need to instantiate an `AsyncTavilyClient` instead. The asynchronous client's interface is identical to the synchronous client's, the only difference being that all methods are asynchronous.

## Methods

* **`search`**(query, **kwargs)
  * Performs a Tavily Search query and returns the response as a well-structured `dict`.
  * **Additional parameters** can be provided as keyword arguments (detailed below). The keyword arguments supported by this method are: `search_depth`, `topic`, `days`,`max_results`, `include_domains`, `exclude_domains`, `include_answer`, `include_raw_content`, `include_images`, `include_image_descriptions`. 
  * **Returns** a `dict` with all related response fields. If you decide to use the asynchronous client, returns a `coroutine` resolving to that `dict`.
* **`get_search_context`**(query, **kwargs)
  * Performs a Tavily Search query and returns a `str` of content and sources within the provided token limit. It's useful for getting only related content from retrieved websites without having to deal with context extraction and token management.
  * The **core parameter** for this function is `max_tokens`, an `int`. It defaults to `4000`. It is provided as a keyword argument.
  * **Returns** a `str` containing the content and sources of the results. If you decide to use the asynchronous client, returns a `coroutine` resolving to that `str`.
* **`qna_search`**(query, **kwargs)
  * Performs a search and returns a `str` containing an answer to the original query. This is optimal to be used as a tool for AI agents.
  * **Returns** a `str` containing a short answer to the search query. If you decide to use the asynchronous client, returns a `coroutine` resolving to that `str`.

### Keyword Arguments (optional)

* **`search_depth`: str** - The depth of the search. It can be `