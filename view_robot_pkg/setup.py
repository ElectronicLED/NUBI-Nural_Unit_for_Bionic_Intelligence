from setuptools import find_packages, setup
from glob import glob

package_name = 'view_robot_pkg'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', ['launch/view_robot.launch']),
        ('share/' + package_name + '/urdf', ['urdf/robot_description.urdf']),
        ('share/' + package_name + '/rviz', ['rviz/default_view.rviz']),
        ('share/' + package_name + '/meshes', glob('meshes/*')), #include meshes
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='apostolos-ubuntu-pc',
    maintainer_email='apostolos-ubuntu-pc@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
        ],
    },
)
