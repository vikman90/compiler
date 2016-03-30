# Toy compiler in Python

Toy C cross-compiler targeted to ARM, written in Python 3.5.

This project was made for the course *Code Transformation and Optimization* 
taught by Professor Giovanni Agosta at *Politecnico di Milano* on July 2014.

The input language is a subset of C, called C--.

## Usage

Run ```python compiler.py```. It will read ```examples/example.cmm``` and
compile it into ```examples/output.s```.
