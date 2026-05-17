# s-git: Semantic Version Control (AST-Based)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![NARE Labs](https://img.shields.io/badge/Organization-NARE%20Labs-blue.svg)](https://github.com/narelabs)

![s-git demo](video/video.mp4)

> **Line-based diffing is a 50-year-old paradigm. It is time for version control to understand the structure of code, not just the characters on a line.**

**s-git** (Semantic Git) is a next-generation semantic version control CLI tool that tracks the **meaning and AST (Abstract Syntax Tree) mutations** of your codebase, rather than line-by-line text edits. 

Instead of showing green and red text blocks for moving or renaming functions, `s-git` compiles your code into hierarchical semantic nodes, hashes their functional structures, and tracks structural modifications, signature adjustments, refactorings, renames, and moves across classes and modules.

---

## 🧬 Why s-git?

| Traditional Git | s-git (Semantic Version Control) |
| :--- | :--- |
| **Text-Based (Line diffs):** Compares strings of text. If you move a function, it treats it as a massive deletion and insertion. | **Structure-Based (AST diffs):** Compares Abstract Syntax Trees. Recognizes that a function was relocated across modules. |
| **Line-Level Conflicts:** If two developers touch different parts of the same file, Git triggers a merge conflict. | **Node-Level Merging:** If developers edit separate methods in the same file, `s-git` merges them automatically without conflicts. |
| **Cryptic Commits:** Developers write generic `fix` or `update` messages. | **Intent-Based Auto-Commits:** Generates precise, human-grade commit messages describing actual AST mutations. |

---

## ⚡ Key Features

*   **Semantic Diffing (`sgit diff`)**: Detects additions, modifications, removals, signature mutations, renames, and migrations of classes, methods, and functions.
*   **Three-Way AST Merging (`sgit merge`)**: Merges separate branches by analyzing functional overlapping. If changes touch different semantic nodes in the same file, they merge automatically without generating textual conflicts.
*   **Intent-Based Auto-Commits (`sgit commit`)**: Automatically generates descriptive, human-readable commit messages by summarizing the exact AST delta.
*   **Local AST Storage**: Saves changes as compressed semantic snapshots inside `.sgit` instead of storing plain files.

---

## 🛠️ Architecture Overview

```
                          ┌────────────────────────┐
                          │    Source Files (.py)   │
                          └───────────┬────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │  AST Parser & Flattener      │
                       │  (Generates SemanticNodes)   │
                       └──────────────┬───────────────┘
                                      │
                                      ▼
                       ┌──────────────────────────────┐
                       │    Semantic Hashing Engine   │
                       │   (Stable node signature)    │
                       └──────────────┬───────────────┘
                                      │
             ┌────────────────────────┴────────────────────────┐
             ▼                                                 ▼
┌──────────────────────────┐                      ┌──────────────────────────┐
│  Semantic Diff Engine    │                      │  Three-Way Merge Engine  │
│  (Matches, Renames,      │                      │   (Resolves non-overlap  │
│   Moves, Delta Computes) │                      │   AST changes cleanly)   │
└────────────┬─────────────┘                      └────────────┬─────────────┘
             │                                                 │
             ▼                                                 ▼
┌──────────────────────────┐                      ┌──────────────────────────┐
│ Auto-Commit Generator    │                      │    AST Snapshot Storage  │
│ (Human-readable messages)│                      │    (.sgit Object Db)     │
└──────────────────────────┘                      └──────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Installation

Install the package in editable mode from the root directory:
```bash
pip install -e .
```

### 2. Initialize a Semantic Repository
Initialize `s-git` in your project folder (it works perfectly alongside standard `.git`!):
```bash
sgit init
```

### 3. Track and Stage Code
Stage your Python files:
```bash
sgit add main.py utils.py
```
*(Use `sgit status` to see staged and untracked semantic files).*

### 4. Create an Intent-Based Commit
Run commit without arguments. `s-git` will automatically generate a descriptive, human-grade commit message summarizing the AST modifications:
```bash
sgit commit
```
**Example Output:**
```text
[main d388a75b] Add 2 elements; Update 1 element
  1 file(s) committed
```

### 5. View Semantic Diffs
Make structural modifications to your code (e.g., change a function signature, rename a method, or add a class) and run:
```bash
sgit diff
```
**Example Output:**
```text
diff --git a/math_utils.py b/math_utils.py
+ Added class 'Calculator'
+ Added method 'Calculator.solve'
  signature: (self, x)
~ Modified function 'add'
  signature changed: (a, b) -> (a, b, c=...)
> Renamed 'multiply' -> 'scale_value'
```

---

## 📂 Project Structure

*   [`cli.py`](file:///c:/Users/danik/Documents/Field/modules/semanticgit/src/sgit/cli.py): The user interface wrapper powered by Click.
*   [`ast_parser.py`](file:///c:/Users/danik/Documents/Field/modules/semanticgit/src/sgit/ast_parser.py): Translates raw Python source files into clean hierarchical `SemanticNode` trees.
*   [`diff_engine.py`](file:///c:/Users/danik/Documents/Field/modules/semanticgit/src/sgit/diff_engine.py): Compares AST snapshots, detects structural modifications, and handles rename/migration similarity checks.
*   [`merge_engine.py`](file:///c:/Users/danik/Documents/Field/modules/semanticgit/src/sgit/merge_engine.py): Performs three-way AST merging.
*   [`storage.py`](file:///c:/Users/danik/Documents/Field/modules/semanticgit/src/sgit/storage.py): Manages local object mapping, branches, logs, indexing, and the `.sgit` folder structure.
*   [`commit_gen.py`](file:///c:/Users/danik/Documents/Field/modules/semanticgit/src/sgit/commit_gen.py): Houses the deterministic, human-readable semantic message builder.

---

## 🧠 The NARE Labs Cognitive Ecosystem

`s-git` is designed as a core component of the **NARE Labs Cognitive Ecosystem**—a suite of advanced, light-weight, deep-tech toolsets pushing the boundary of artificial intelligence, code reasoning, and neural architectures:

*   [**sr-moa**](https://github.com/narelabs/sr-moa): Self-Reflective Mixture of Adapters. A PyTorch-based test-time optimization (TTT) framework enabling models to self-correct their weights at runtime on errors.
*   [**dsm**](https://github.com/narelabs/dsm): Dynamic Segmented Memory. A lightning-fast, segmented, hierarchical vector graph memory designed for persistent agent context without token bloat.

---

## 📄 License

This project is licensed under the MIT License.

---

## ✉️ Citation

If you use `s-git` in your development pipeline, research, or organizational environments, please cite the creator:

```bibtex
@software{vladov_sgit_2026,
  author       = {Danil Vladov},
  title        = {s-git: High-Performance AST-Based Semantic Version Control CLI},
  institution  = {NARE Labs},
  year         = {2026},
  publisher    = {GitHub},
  journal      = {GitHub Repository},
  howpublished = {\url{https://github.com/narelabs/s-git}}
}
```
