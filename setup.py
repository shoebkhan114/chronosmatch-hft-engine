from setuptools import setup, Extension
from Cython.Build import cythonize

setup(
    name="chronosmatch-cython",
    ext_modules=cythonize(
        [Extension("src.matching_engine_cy", ["src/matching_engine_cy.pyx"])],
        language_level=3,
    ),
)
