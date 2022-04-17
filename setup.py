import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(name='qmc5883l',
                 version='1.0.7',
                 author='Yanfu Zhou',
                 author_email='yanfu.zhou@outlook.com',
                 description='Driver for qmc5883l 3-Axis Magnetic Sensor',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url='http://github.com/yanfuzhou/qmc5883l',
                 download_url='http://github.com/yanfuzhou/qmc5883l/archive/1.0.7.tar.gz)',
                 license='MIT',
                 packages=setuptools.find_packages(),
                 classifiers=[
                       "Programming Language :: Python",
                       "License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
                       "Operating System :: OS Independent",
                 ],
                 zip_safe=False)
