from setuptools import find_packages, setup

package_name = 'ros2_stm_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='mohab',
    maintainer_email='mohabsalah15@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "publisher_stm = ros2_stm_pkg.publisher_stm:main",
            "subscriber_stm = ros2_stm_pkg.subscriber_stm:main"
        ],
    },
)
