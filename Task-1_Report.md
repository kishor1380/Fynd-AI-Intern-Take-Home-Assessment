
# Rating Prediction Using Prompts: A Simple Analysis

## Summary

I tested three different ways to get an AI model to predict star ratings (1-5 stars) for Yelp reviews. I used 200 reviews and tried each method to see which works best. The Chain-of-Thought approach worked the best overall - it got 56.5% accuracy and never failed to give me proper JSON output. This makes it the most reliable choice for real-world use.

## What I Tried to Do

### Main Goal
My task was to design different prompts that would help the AI predict what star rating a customer gave to their Yelp review. The AI also needed to explain why it chose that rating.

### How I Measured Success
I looked at four things:
1. **Accuracy**: How often the prediction matched the actual rating
2. **Mean Absolute Error (MAE)**: How far off the predictions were on average
3. **JSON Validity**: Whether the AI's response could be properly read and parsed
4. **Consistency**: How well it handled tricky reviews with mixed feelings

### The Dataset
I used Yelp reviews from Kaggle. I picked 200 reviews total - about 40 from each star rating (1-5 stars). The reviews ranged from short ones (50 words) to longer ones (300+ words).

---

## The Three Approaches I Tested

### Approach 1: Simple Zero-Shot

**What It Is**
This is the most basic approach. I just told the AI what to do without giving it examples or special instructions.

**The Prompt**
I wrote something like: "You rate customer reviews. Read this Yelp review and tell me how many stars (1-5) the customer probably gave. Give me a JSON with predicted_stars and explanation."

**Why I Tried This**
I wanted to see how well the AI could do the task naturally, without any special help. This gives me a baseline to compare the other methods against.

**What I Expected**
- Good: Simple and quick, uses fewer words
- Bad: Might make formatting mistakes, explanations could be inconsistent

### Approach 2: Structured with Examples

**What It Is**
Here I gave the AI explicit instructions about the format I wanted. I showed it examples of good responses and told it exactly what not to do.

**The Prompt**
I told it: "You classify reviews into ratings 1-5. Read the review, pick a rating, and return strict JSON. Don't add extra stuff. Here are examples of what I want: {examples}. Now classify this review."

**Why I Tried This**
I thought giving clear rules and examples would force the AI to stick to the format and avoid mistakes.

**What I Expected**
- Good: Clear instructions should reduce errors
- Bad: Longer prompt might confuse it or make it too rigid

### Approach 3: Chain-of-Thought

**What It Is**
This approach asks the AI to think through the problem step-by-step first, then give me just the final answer in JSON.

**The Prompt**
I wrote: "You're a sentiment analyst. First, think about: is it positive or negative? How strong? What specific things did they mention? Would they recommend it? Then output ONLY a JSON object - don't show me your thinking."

**Why I Tried This**
Reviews can be tricky - sometimes people say both good and bad things. I wanted the AI to reason through it carefully before deciding. But I also wanted clean JSON output at the end.

**What I Expected**
- Good: Better at handling mixed reviews, cleaner output
- Bad: Uses more tokens, AI needs to suppress its thinking

---

## Results

### Overall Performance

| Approach | Accuracy | MAE | JSON Worked | Samples |
|----------|----------|-----|-------------|---------|
| Zero-Shot | 57.5% | 0.48 | 98.5% | 200 |
| Structured | 39.0% | 0.83 | 25.5% | 200 |
| Chain-of-Thought | 56.5% | 0.49 | 100% | 200 |

### What the Numbers Mean

**Accuracy**
The simple zero-shot approach actually did best at 57.5%. This surprised me - it means the AI already knows how to analyze reviews pretty well without extra help. 

Chain-of-thought came close at 56.5%. The thinking step didn't improve accuracy much, but it did help with consistency.

The structured approach failed badly at 39%. I'll explain why below.

**JSON Validity - The Big Surprise**
This is where things got interesting:
- Chain-of-thought: 100% - never failed to give me clean JSON
- Zero-shot: 98.5% - almost always worked
- Structured: 25.5% - failed most of the time!

This was weird. I gave the structured approach the most specific instructions about formatting, but it failed the most. When JSON parsing failed, my code defaulted to predicting 3 stars (neutral), which killed the accuracy.

**Why Did Structured Fail?**
I think giving too many rules actually confused the AI. Even though I said "don't add extra text," it kept adding explanations outside the JSON. The stricter I was, the worse it got. 

Meanwhile, chain-of-thought worked by being more natural. Saying "output ONLY a JSON object" worked better than listing a bunch of rules.

### Looking at Specific Ratings

| Rating | Zero-Shot | Structured | Chain-of-Thought |
|--------|-----------|------------|------------------|
| 1-Star | 72.5% | 10.0% | 70.0% |
| 2-Star | 42.5% | 5.0% | 45.0% |
| 3-Star | 55.0% | 92.5% | 50.0% |
| 4-Star | 60.0% | 10.0% | 60.0% |
| 5-Star | 55.0% | 5.0% | 60.0% |

The structured approach shows a clear problem - it predicted 3 stars way too often (92.5% of the time for actual 3-star reviews, but almost never for other ratings). This confirms the JSON failures were causing fallback predictions.

Zero-shot and chain-of-thought were more balanced. They did slightly better on extreme ratings (1 and 5 stars) because those reviews usually have clearer sentiment.

---

## Example Predictions

### Example 1: Very Negative Review

**Review**: "The only reason 1 star can be given is the flavor was terrible... will never going to recommend to anyone anymore..."

**Actual Rating**: 1 star

All three approaches got this right. The negative language was so strong that it was easy to classify.

### Example 2: Mixed Feelings Review

**Review**: "I used to come here often... noticed a slide in quality... but I hope they had a weak day..."

**Actual Rating**: 2 stars

- **Zero-shot predicted**: 3 stars - it saw both complaints and hope, so it went neutral
- **Structured predicted**: 3 stars (but this was a parsing failure, not real analysis)
- **Chain-of-thought predicted**: 2 stars ✓ - it recognized that despite hope for improvement, the current experience deserved a lower rating

This shows where chain-of-thought helps. It understood the nuance better.

---

## Key Findings

### 1. Simple Sometimes Wins
The simplest approach (zero-shot) got the best accuracy. This tells me the AI model (Gemini-1.5-flash in my case) is already pretty good at understanding reviews. Sometimes adding complexity doesn't help much.

### 2. Too Many Rules Backfire
I learned that being too specific about formatting can actually make things worse. The structured approach with all its rules performed the worst. Natural language like "output ONLY" works better than formal rules like "do not include extra keys."

### 3. Chain-of-Thought Is Most Reliable
Even though chain-of-thought didn't have the highest accuracy, it's the best choice for actual use because:
- It never failed to give proper JSON (100%)
- Accuracy was still good (56.5%)
- It handled tricky reviews better
- No risk of parsing failures

### 4. Understanding the Limits
All three approaches hit around 55-58% accuracy. To go higher, I'd probably need:
- More context or examples in the prompt
- A model trained specifically on Yelp reviews
- Multiple AI models working together

---

## What I Learned

### About Prompting
1. Natural language instructions work better than formal rules
2. Telling the AI to "think step-by-step" then "output only JSON" creates a clean separation
3. Shorter prompts can sometimes work better than longer, detailed ones
4. Examples can help, but too many constraints can confuse the model

### About JSON Output
The biggest lesson was about getting structured output. I learned that:
- Phrase instructions naturally ("output ONLY a JSON object")
- Separate thinking from output explicitly
- Don't over-specify formatting rules
- Test the JSON parsing rate, not just accuracy

### About the Task
Predicting star ratings is hard because:
- Reviews with mixed sentiment are common
- Sometimes people say positive things but give low ratings (or vice versa)
- Sarcasm is difficult to detect
- Context matters (what's "good" for fast food vs fine dining is different)

---

## Recommendation

For anyone wanting to use this in production, I'd recommend the **Chain-of-Thought Constrained approach**. Here's why:

1. **It's reliable**: 100% JSON validity means your code never breaks
2. **It's accurate enough**: 56.5% is close to the best (57.5%)
3. **It handles edge cases**: The reasoning step helps with nuanced reviews
4. **It's debuggable**: You can modify it to show reasoning when needed

The zero-shot approach is also fine if you want maximum simplicity and can tolerate occasional JSON parsing failures (1.5% failure rate).

Don't use the structured approach - the low JSON validity makes it unusable despite good intentions.

---

## Limitations and Future Work

### What Could Be Better
- I only tested 200 reviews - more samples would give more confidence
- I used one model (Gemini-1.5-flash) - other models might behave differently
- I didn't test prompt variations (temperature, max tokens, etc.)
- The reviews were in English only

### What I'd Try Next
1. Test with more review samples (1000+)
2. Try different AI models and compare
3. Experiment with few-shot learning (giving examples in the prompt)
4. Fine-tune a model specifically on Yelp reviews
5. Try ensemble methods (combining multiple approaches)
6. Add domain-specific context (restaurant vs hotel vs shop)

---

## Conclusion

I tested three prompting strategies for predicting Yelp star ratings. The simplest approach surprisingly worked best for pure accuracy (57.5%), but the chain-of-thought approach is the most practical for real use because it never fails to produce parseable output (100% JSON validity) while maintaining good accuracy (56.5%).

The structured approach taught me an important lesson: more rules don't always help. Sometimes being overly specific can confuse the AI and hurt performance.

For this task, I'd use chain-of-thought in production. It's reliable, accurate enough, and handles tricky reviews well. But if you need absolute maximum accuracy and can handle occasional parsing errors, the simple zero-shot approach is worth considering too.

The main takeaway: when designing prompts, focus on natural language and clear separation of reasoning from output, rather than trying to control every detail with formal rules.
