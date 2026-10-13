"""Core package; import implementations from their explicit modules.

Avoid eager model/vector imports so lightweight utilities and health tooling
can start and be tested without loading the entire AI dependency stack.
"""
