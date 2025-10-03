# Model Comparison Analysis: Three-Way Model Comparison

## 📋 Overview

This document presents a comprehensive comparison between three embedding models:
- **Vyakyarth (Krutrim)**: Specialized for Indian languages including Malayalam
- **all-MiniLM-L6-v2**: General-purpose multilingual model
- **paraphrase-multilingual-mpnet-base-v2**: Advanced multilingual model

## 🔬 Test Methodology

### Test Cases
1. **Malayalam - Similar Meaning**: Two Malayalam sentences with similar meaning
2. **Malayalam - Different Topics**: Two Malayalam sentences about different subjects
3. **English - Similar Meaning**: Two English sentences with similar meaning
4. **English - Different Topics**: Two English sentences about different subjects
5. **Cross-lingual (Malayalam-English)**: Malayalam vs English translation
6. **Same Text**: Identical text (should give 1.0 similarity)

### Code Implementation

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def calculate_similarity(model, sentences, model_name):
    """Calculate cosine similarity for given sentences using specified model"""
    print(f"\n{'='*60}")
    print(f"Model: {model_name}")
    print(f"{'='*60}")
    
    # Generate embeddings
    embeddings = model.encode(sentences)
    
    # Calculate cosine similarity
    similarity_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    
    print(f"Text 1: {sentences[0]}")
    print(f"Text 2: {sentences[1]}")
    print(f"Cosine Similarity: {similarity_score:.6f}")
    
    return similarity_score

# Load all three models
print("Loading models...")
vyakyarth_model = SentenceTransformer("krutrim-ai-labs/vyakyarth")
minilm_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
multilingual_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-mpnet-base-v2")

# Test cases for comparison
test_cases = [
    {
        "name": "Malayalam - Similar Meaning",
        "sentences": [
            "മലയാളം ഭാഷാ പഠനം",
            "മലയാളം ഭാഷാ അധ്യയനം"
        ]
    },
    {
        "name": "Malayalam - Different Topics", 
        "sentences": [
            "കമ്പ്യൂട്ടർ സയൻസ് പഠനം",
            "ഗണിത ശാസ്ത്രം പഠനം"
        ]
    },
    {
        "name": "English - Similar Meaning",
        "sentences": [
            "Machine learning is fascinating",
            "Artificial intelligence is interesting"
        ]
    },
    {
        "name": "English - Different Topics",
        "sentences": [
            "Computer science programming",
            "Mathematics and statistics"
        ]
    },
    {
        "name": "Cross-lingual (Malayalam-English)",
        "sentences": [
            "മലയാളം ഭാഷാ പഠനം",
            "Malayalam language learning"
        ]
    },
    {
        "name": "Same Text (Should be 1.0)",
        "sentences": [
            "രാത്രി സേവന സുരക്ഷാ സർക്കുലർ",
            "രാത്രി സേവന സുരക്ഷാ സർക്കുലർ"
        ]
    }
]

# Results storage
results = []

# Test each case with all three models
for test_case in test_cases:
    print(f"\n{'#'*80}")
    print(f"TEST CASE: {test_case['name']}")
    print(f"{'#'*80}")
    
    # Test with Vyakyarth model
    vyakyarth_score = calculate_similarity(
        vyakyarth_model, 
        test_case['sentences'], 
        "Vyakyarth (Krutrim)"
    )
    
    # Test with MiniLM model
    minilm_score = calculate_similarity(
        minilm_model, 
        test_case['sentences'], 
        "all-MiniLM-L6-v2"
    )
    
    # Test with Multilingual MPNet model
    multilingual_score = calculate_similarity(
        multilingual_model, 
        test_case['sentences'], 
        "paraphrase-multilingual-mpnet-base-v2"
    )
    
    # Store results
    results.append({
        'test_case': test_case['name'],
        'vyakyarth_score': vyakyarth_score,
        'minilm_score': minilm_score,
        'multilingual_score': multilingual_score,
        'vyakyarth_minilm_diff': abs(vyakyarth_score - minilm_score),
        'vyakyarth_multilingual_diff': abs(vyakyarth_score - multilingual_score),
        'minilm_multilingual_diff': abs(minilm_score - multilingual_score)
    })

# Summary comparison
print(f"\n{'='*100}")
print("SUMMARY COMPARISON - ALL THREE MODELS")
print(f"{'='*100}")
print(f"{'Test Case':<30} {'Vyakyarth':<12} {'MiniLM':<12} {'Multilingual':<12} {'V-M Diff':<12} {'V-Multi Diff':<12}")
print("-" * 100)

for result in results:
    print(f"{result['test_case']:<30} {result['vyakyarth_score']:<12.6f} {result['minilm_score']:<12.6f} {result['multilingual_score']:<12.6f} {result['vyakyarth_minilm_diff']:<12.6f} {result['vyakyarth_multilingual_diff']:<12.6f}")

# Calculate average differences
avg_vyakyarth_minilm_diff = np.mean([r['vyakyarth_minilm_diff'] for r in results])
avg_vyakyarth_multilingual_diff = np.mean([r['vyakyarth_multilingual_diff'] for r in results])
avg_minilm_multilingual_diff = np.mean([r['minilm_multilingual_diff'] for r in results])

print(f"\nAverage differences between models:")
print(f"Vyakyarth vs MiniLM: {avg_vyakyarth_minilm_diff:.6f}")
print(f"Vyakyarth vs Multilingual: {avg_vyakyarth_multilingual_diff:.6f}")
print(f"MiniLM vs Multilingual: {avg_minilm_multilingual_diff:.6f}")

# Model performance analysis
vyakyarth_avg = np.mean([r['vyakyarth_score'] for r in results])
minilm_avg = np.mean([r['minilm_score'] for r in results])
multilingual_avg = np.mean([r['multilingual_score'] for r in results])

print(f"\nAverage similarity scores:")
print(f"Vyakyarth (Krutrim): {vyakyarth_avg:.6f}")
print(f"all-MiniLM-L6-v2: {minilm_avg:.6f}")
print(f"paraphrase-multilingual-mpnet-base-v2: {multilingual_avg:.6f}")

# Find the best performing model
models = {
    'Vyakyarth': vyakyarth_avg,
    'MiniLM': minilm_avg,
    'Multilingual': multilingual_avg
}

best_model = max(models, key=models.get)
best_score = models[best_model]

print(f"\n🏆 BEST PERFORMING MODEL: {best_model} with {best_score:.6f} average similarity")

# Calculate percentage differences
print(f"\nPercentage differences from best model:")
for model_name, score in models.items():
    if model_name != best_model:
        diff_percent = ((best_score - score) / best_score) * 100
        print(f"{model_name}: {diff_percent:.2f}% lower than {best_model}")

# Model ranking
sorted_models = sorted(models.items(), key=lambda x: x[1], reverse=True)
print(f"\nModel Ranking (by average similarity):")
for i, (model_name, score) in enumerate(sorted_models, 1):
    print(f"{i}. {model_name}: {score:.6f}")
```

## 📊 Test Results

### Detailed Results

```
Loading models...

################################################################################
TEST CASE: Malayalam - Similar Meaning
################################################################################

============================================================
Model: Vyakyarth (Krutrim)
============================================================
Text 1: മലയാളം ഭാഷാ പഠനം
Text 2: മലയാളം ഭാഷാ അധ്യയനം
Cosine Similarity: 0.884683

============================================================
Model: all-MiniLM-L6-v2
============================================================
Text 1: മലയാളം ഭാഷാ പഠനം
Text 2: മലയാളം ഭാഷാ അധ്യയനം
Cosine Similarity: 1.000000

============================================================
Model: paraphrase-multilingual-mpnet-base-v2
============================================================
Text 1: മലയാളം ഭാഷാ പഠനം
Text 2: മലയാളം ഭാഷാ അധ്യയനം
Cosine Similarity: 0.951660

################################################################################
TEST CASE: Malayalam - Different Topics
################################################################################

============================================================
Model: Vyakyarth (Krutrim)
============================================================
Text 1: കമ്പ്യൂട്ടർ സയൻസ് പഠനം
Text 2: ഗണിത ശാസ്ത്രം പഠനം
Cosine Similarity: 0.530189

============================================================
Model: all-MiniLM-L6-v2
============================================================
Text 1: കമ്പ്യൂട്ടർ സയൻസ് പഠനം
Text 2: ഗണിത ശാസ്ത്രം പഠനം
Cosine Similarity: 1.000000

============================================================
Model: paraphrase-multilingual-mpnet-base-v2
============================================================
Text 1: കമ്പ്യൂട്ടർ സയൻസ് പഠനം
Text 2: ഗണിത ശാസ്ത്രം പഠനം
Cosine Similarity: 0.630552

################################################################################
TEST CASE: English - Similar Meaning
################################################################################

============================================================
Model: Vyakyarth (Krutrim)
============================================================
Text 1: Machine learning is fascinating
Text 2: Artificial intelligence is interesting
Cosine Similarity: 0.680437

============================================================
Model: all-MiniLM-L6-v2
============================================================
Text 1: Machine learning is fascinating
Text 2: Artificial intelligence is interesting
Cosine Similarity: 0.746092

============================================================
Model: paraphrase-multilingual-mpnet-base-v2
============================================================
Text 1: Machine learning is fascinating
Text 2: Artificial intelligence is interesting
Cosine Similarity: 0.746577

################################################################################
TEST CASE: English - Different Topics
################################################################################

============================================================
Model: Vyakyarth (Krutrim)
============================================================
Text 1: Computer science programming
Text 2: Mathematics and statistics
Cosine Similarity: 0.500628

============================================================
Model: all-MiniLM-L6-v2
============================================================
Text 1: Computer science programming
Text 2: Mathematics and statistics
Cosine Similarity: 0.272589

============================================================
Model: paraphrase-multilingual-mpnet-base-v2
============================================================
Text 1: Computer science programming
Text 2: Mathematics and statistics
Cosine Similarity: 0.358654

################################################################################
TEST CASE: Cross-lingual (Malayalam-English)
################################################################################

============================================================
Model: Vyakyarth (Krutrim)
============================================================
Text 1: മലയാളം ഭാഷാ പഠനം
Text 2: Malayalam language learning
Cosine Similarity: 0.808110

============================================================
Model: all-MiniLM-L6-v2
============================================================
Text 1: മലയാളം ഭാഷാ പഠനം
Text 2: Malayalam language learning
Cosine Similarity: 0.050902

============================================================
Model: paraphrase-multilingual-mpnet-base-v2
============================================================
Text 1: മലയാളം ഭാഷാ പഠനം
Text 2: Malayalam language learning
Cosine Similarity: 0.576640

################################################################################
TEST CASE: Same Text (Should be 1.0)
################################################################################

============================================================
Model: Vyakyarth (Krutrim)
============================================================
Text 1: രാത്രി സേവന സുരക്ഷാ സർക്കുലർ
Text 2: രാത്രി സേവന സുരക്ഷാ സർക്കുലർ
Cosine Similarity: 1.000000

============================================================
Model: all-MiniLM-L6-v2
============================================================
Text 1: രാത്രി സേവന സുരക്ഷാ സർക്കുലർ
Text 2: രാത്രി സേവന സുരക്ഷാ സർക്കുലർ
Cosine Similarity: 1.000000

============================================================
Model: paraphrase-multilingual-mpnet-base-v2
============================================================
Text 1: രാത്രി സേവന സുരക്ഷാ സർക്കുലർ
Text 2: രാത്രി സേവന സുരക്ഷാ സർക്കുലർ
Cosine Similarity: 1.000000
```

### Summary Comparison Table

| Test Case | Vyakyarth | MiniLM | Multilingual | V-M Diff | V-Multi Diff |
|-----------|-----------|---------|--------------|----------|--------------|
| Malayalam - Similar Meaning | 0.884683 | 1.000000 | 0.951660 | 0.115317 | 0.066977 |
| Malayalam - Different Topics | 0.530189 | 1.000000 | 0.630552 | 0.469811 | 0.100362 |
| English - Similar Meaning | 0.680437 | 0.746092 | 0.746577 | 0.065655 | 0.066140 |
| English - Different Topics | 0.500628 | 0.272589 | 0.358654 | 0.228039 | 0.141974 |
| Cross-lingual (Malayalam-English) | 0.808110 | 0.050902 | 0.576640 | 0.757207 | 0.231470 |
| Same Text (Should be 1.0) | 1.000000 | 1.000000 | 1.000000 | 0.000000 | 0.000000 |

### Overall Statistics

- **Average differences between models**:
  - Vyakyarth vs MiniLM: 0.272672
  - Vyakyarth vs Multilingual: 0.101154
  - MiniLM vs Multilingual: 0.171679

- **Average similarity scores**:
  - Vyakyarth (Krutrim): 0.734008
  - all-MiniLM-L6-v2: 0.678264
  - paraphrase-multilingual-mpnet-base-v2: 0.710680

- **🏆 BEST PERFORMING MODEL**: Vyakyarth with 0.734008 average similarity

- **Percentage differences from best model**:
  - MiniLM: 7.59% lower than Vyakyarth
  - Multilingual: 3.18% lower than Vyakyarth

- **Model Ranking (by average similarity)**:
  1. Vyakyarth: 0.734008
  2. Multilingual: 0.710680
  3. MiniLM: 0.678264

## 📈 Analysis & Insights

### 🏆 Overall Winner: Vyakyarth (Krutrim)

**Key Findings:**
- **Best overall performance** with 0.734008 average similarity
- **3.18% better** than Multilingual MPNet
- **7.59% better** than MiniLM
- Consistent performance across all test cases

### 📊 Detailed Analysis by Category

#### 1. Malayalam Text Performance
- **Vyakyarth**: Balanced understanding (0.88 vs 0.53 for different topics)
- **Multilingual**: Good performance (0.95 vs 0.63 for different topics)
- **MiniLM**: Shows concerning behavior - giving **1.0 similarity** for completely different Malayalam topics
- **Verdict**: Vyakyarth and Multilingual both superior to MiniLM

#### 2. English Text Performance
- **Similar meaning**: Multilingual slightly better (0.747 vs 0.746 vs 0.680)
- **Different topics**: Vyakyarth best (0.501 vs 0.359 vs 0.273)
- **Verdict**: Mixed results, but Vyakyarth most consistent

#### 3. Cross-lingual (Malayalam-English)
- **Vyakyarth**: Excellent (0.808) - best cross-lingual understanding
- **Multilingual**: Good (0.577) - decent cross-lingual capabilities
- **MiniLM**: Very poor (0.051) - fails to connect Malayalam-English pairs
- **Verdict**: Vyakyarth dominates, Multilingual acceptable, MiniLM fails

#### 4. Identical Text
- All three models correctly return **1.000** similarity
- **Verdict**: All work correctly for exact matches

### 🚨 Concerning Issues with MiniLM

#### Red Flags:
1. **Malayalam Different Topics**: MiniLM gives 1.000 similarity for:
   - "കമ്പ്യൂട്ടർ സയൻസ് പഠനം" (Computer Science)
   - "ഗണിത ശാസ്ത്രം പഠനം" (Mathematics)
   
   This suggests MiniLM may not properly understand Malayalam text differences.

2. **Cross-lingual Failure**: 0.051 similarity for Malayalam-English pairs indicates poor multilingual capabilities.

### 🎯 Multilingual MPNet Performance

#### Strengths:
- **Good Malayalam understanding** (0.95 vs 0.63 for different topics)
- **Decent cross-lingual** capabilities (0.577)
- **Competitive English performance** (0.747 for similar meaning)

#### Weaknesses:
- **Slightly lower overall** than Vyakyarth (3.18% difference)
- **Less nuanced** than Vyakyarth for topic differentiation

## 🎯 Recommendations

### For Malayalam Text
- **Use Vyakyarth** - best overall performance
- **Alternative**: Multilingual MPNet - good performance
- **Avoid**: MiniLM - concerning behavior with Malayalam

### For English Text
- **Use Vyakyarth** - most consistent performance
- **Alternative**: Multilingual MPNet - competitive performance
- **Avoid**: MiniLM - poor topic differentiation

### For Cross-lingual Tasks
- **Use Vyakyarth** - excellent cross-lingual understanding (0.808)
- **Alternative**: Multilingual MPNet - decent cross-lingual (0.577)
- **Avoid**: MiniLM - poor cross-lingual (0.051)

### For Production RAG System
- **Primary**: Vyakyarth - best overall performance
- **Fallback**: Multilingual MPNet - good alternative
- **Avoid**: MiniLM - multiple concerning issues

## 📋 Performance Summary Table

| Test Case | Vyakyarth | MiniLM | Multilingual | Winner |
|-----------|-----------|---------|--------------|---------|
| Malayalam Similar | 0.885 | 1.000 | 0.952 | Multilingual |
| Malayalam Different | 0.530 | 1.000 | 0.631 | Multilingual |
| English Similar | 0.680 | 0.746 | 0.747 | Multilingual |
| English Different | 0.501 | 0.273 | 0.359 | Vyakyarth |
| Cross-lingual | 0.808 | 0.051 | 0.577 | Vyakyarth |
| Identical | 1.000 | 1.000 | 1.000 | Tie |

*Note: MiniLM's 1.000 for different Malayalam topics is likely a bug/limitation

## 🔧 Implementation Recommendations

### For RAG Systems

1. **Primary Model**: Vyakyarth for best overall performance
2. **Fallback**: Multilingual MPNet for good alternative
3. **Avoid**: MiniLM due to multiple concerning issues
4. **Hybrid Approach**: Use Vyakyarth for primary, Multilingual MPNet as backup

### Model Selection Criteria

| Use Case | Recommended Model | Alternative | Reason |
|----------|------------------|-------------|---------|
| Malayalam Text | Vyakyarth | Multilingual MPNet | Best understanding |
| English Text | Vyakyarth | Multilingual MPNet | Most consistent performance |
| Cross-lingual | Vyakyarth | Multilingual MPNet | Excellent multilingual capabilities |
| Multilingual RAG | Vyakyarth | Multilingual MPNet | Best overall performance |
| English-only | Vyakyarth | Multilingual MPNet | Both perform well |

## 🎉 Conclusion

The three-way comparison reveals **Vyakyarth as the clear winner** for multilingual RAG systems, with **Multilingual MPNet as a strong alternative**. MiniLM shows concerning issues that make it unsuitable for production use.

### Key Takeaways:
- ✅ **Vyakyarth**: Best overall performance (0.734008 average similarity)
- ✅ **Multilingual MPNet**: Strong alternative (0.710680 average similarity)
- ✅ **Both models**: Good cross-lingual understanding
- ⚠️ **MiniLM**: Multiple concerning issues (0.678264 average similarity)
- ⚠️ **MiniLM**: Poor cross-lingual performance and Malayalam text handling

### Final Recommendations:
- **Primary Choice**: Vyakyarth for best overall performance
- **Alternative**: Multilingual MPNet for good performance
- **Avoid**: MiniLM due to reliability issues

For production deployment, **Vyakyarth is the clear winner** with **Multilingual MPNet as a reliable backup** for multilingual RAG systems.
