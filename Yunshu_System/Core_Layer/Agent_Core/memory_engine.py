import json
import math
import os
import re
from pathlib import Path
from collections import Counter

class SimpleBM25:
    """
    A lightweight, dependency-free BM25 implementation for Chinese text.
    Uses character-based bigrams for tokenization.
    """
    def __init__(self, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.avgdl = 0
        self.doc_count = 0
        self.idf = {}
        self.doc_lengths = []
        self.documents = [] # Metadata for retrieval

    def _tokenize(self, text):
        """Character-based bigrams for Chinese."""
        # Remove non-word characters
        text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)
        if len(text) < 2:
            return [text]
        return [text[i:i+2] for i in range(len(text)-1)]

    def fit(self, documents):
        """
        Build index from documents.
        documents: list of dict {'content': str, 'meta': dict}
        """
        self.documents = documents
        self.doc_count = len(documents)
        self.doc_lengths = []
        doc_term_counts = []
        
        total_length = 0
        
        # 1. Count terms
        for doc in documents:
            terms = self._tokenize(doc['content'])
            length = len(terms)
            self.doc_lengths.append(length)
            total_length += length
            doc_term_counts.append(Counter(terms))
            
        self.avgdl = total_length / self.doc_count if self.doc_count > 0 else 0
        
        # 2. Calculate IDF
        df = Counter()
        for term_counts in doc_term_counts:
            df.update(term_counts.keys())
            
        self.idf = {}
        for term, freq in df.items():
            # Standard IDF formula
            self.idf[term] = math.log((self.doc_count - freq + 0.5) / (freq + 0.5) + 1)

        # 3. Store term counts for scoring (In-memory inverted index optimization could go here)
        self.doc_term_counts = doc_term_counts

    def search(self, query, top_k=3):
        """Search and return top_k results."""
        query_terms = self._tokenize(query)
        scores = []
        
        for i in range(self.doc_count):
            score = 0
            doc_len = self.doc_lengths[i]
            term_counts = self.doc_term_counts[i]
            
            for term in query_terms:
                if term not in self.idf:
                    continue
                
                freq = term_counts[term]
                numerator = self.idf[term] * freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)
                score += numerator / denominator
            
            if score > 0:
                scores.append((score, self.documents[i]))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:top_k]

    def save(self, path):
        """Save index to JSON."""
        data = {
            'k1': self.k1,
            'b': self.b,
            'avgdl': self.avgdl,
            'doc_count': self.doc_count,
            'idf': self.idf,
            'doc_lengths': self.doc_lengths,
            'documents': self.documents,
            # Counter objects are not JSON serializable, convert to dict
            'doc_term_counts': [dict(c) for c in self.doc_term_counts]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def load(self, path):
        """Load index from JSON."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.k1 = data['k1']
        self.b = data['b']
        self.avgdl = data['avgdl']
        self.doc_count = data['doc_count']
        self.idf = data['idf']
        self.doc_lengths = data['doc_lengths']
        self.documents = data['documents']
        # Convert dict back to Counter
        self.doc_term_counts = [Counter(c) for c in data['doc_term_counts']]

class MemoryManager:
    """Interface for managing novel memories."""
    
    def __init__(self, novels_root):
        self.novels_root = Path(novels_root)
        self.engines = {} # Cache loaded engines: {novel_name: SimpleBM25}
        self._preload_indices()

    def _preload_indices(self):
        """Try to load existing indices."""
        if not self.novels_root.exists():
            return
            
        for item in self.novels_root.iterdir():
            if item.is_dir():
                novel_name = item.name
                index_path = self._get_index_path(novel_name)
                if index_path.exists():
                    try:
                        engine = SimpleBM25()
                        engine.load(index_path)
                        self.engines[novel_name] = engine
                        print(f"[Memory] Loaded index for {novel_name}")
                    except Exception as e:
                        print(f"[Memory] Failed to load index for {novel_name}: {e}")

    def _get_index_path(self, novel_name):
        return self.novels_root / novel_name / ".yunshu_memory.json"

    def build_novel_index(self, novel_name):
        """Scan a novel directory and build index."""
        novel_dir = self.novels_root / novel_name
        if not novel_dir.exists():
            return False, "Novel directory not found"
        
        documents = []
        
        # Walk through all txt files
        for root, _, files in os.walk(novel_dir):
            for file in files:
                if file.endswith('.txt'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Granularity: Whole chapter for now
                        # Optimization: Split into paragraphs if needed
                        documents.append({
                            'content': content,
                            'meta': {
                                'path': os.path.relpath(file_path, self.novels_root),
                                'filename': file
                            }
                        })
                    except Exception as e:
                        print(f"Error reading {file}: {e}")
        
        if not documents:
            return False, "No documents found"

        engine = SimpleBM25()
        engine.fit(documents)
        
        index_path = self._get_index_path(novel_name)
        engine.save(index_path)
        self.engines[novel_name] = engine
        
        return True, f"Indexed {len(documents)} chapters."

    def query(self, novel_name, query_text, top_k=3):
        """Query memory for a specific novel."""
        # Load if not cached
        if novel_name not in self.engines:
            index_path = self._get_index_path(novel_name)
            if index_path.exists():
                engine = SimpleBM25()
                engine.load(index_path)
                self.engines[novel_name] = engine
            else:
                # Try to build on the fly
                success, msg = self.build_novel_index(novel_name)
                if not success:
                    return []
        
        engine = self.engines[novel_name]
        results = engine.search(query_text, top_k)
        
        # Format results
        formatted = []
        for score, doc in results:
            formatted.append({
                'score': score,
                'novel': novel_name,
                'filename': doc['meta']['filename'],
                'path': doc['meta']['path'],
                # Return a snippet around the match? 
                # For now return start of content or simple slice
                'preview': doc['content'][:200] + "..." 
            })
        return formatted

    def search_all(self, query_text, top_k=3):
        """Search across all loaded novels."""
        all_results = []
        # Ensure we have at least tried to load everything present
        self._preload_indices()
        
        if not self.engines:
            # If no engines loaded, try to build for all subdirs
             if self.novels_root.exists():
                for item in self.novels_root.iterdir():
                    if item.is_dir():
                        self.build_novel_index(item.name)

        for novel_name in self.engines:
            results = self.query(novel_name, query_text, top_k=top_k)
            all_results.extend(results)
            
        # Global sort
        all_results.sort(key=lambda x: x['score'], reverse=True)
        return all_results[:top_k]
