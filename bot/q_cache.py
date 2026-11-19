import os, anthropic
import cachefix
import run as R
c = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
rules = R.RULES.format(today="TODAY (given in CONTEXT)", default_venue="x", city="y")
print("model", R.MODEL, "rules chars", len(rules))
for i in range(2):
    r = c.messages.create(model=R.MODEL, max_tokens=50, system=rules, tools=[R.TOOL],
                          messages=[{"role": "user", "content": "say ok"}])
    u = r.usage
    print(i, "in", u.input_tokens, "write", u.cache_creation_input_tokens, "read", u.cache_read_input_tokens)
