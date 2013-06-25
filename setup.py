from setuptools import setup, find_packages

setup(
    name = "coucher",
    version = "0.1",
    install_requires=["requests", "ijson", "six"],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
)
