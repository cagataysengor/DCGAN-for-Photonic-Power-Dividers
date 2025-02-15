#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 11:10:45 2023

@author: sengor
"""


from matplotlib import pyplot as plt
import numpy as np
import meep.adjoint as mpa
import meep as mp
print(mp.__version__)
import tensorflow as tf
tf.config.list_logical_devices()

seed = 240
np.random.seed(seed)   
mp.verbosity(0)
Si = mp.Medium(index=3.4)
air = mp.Medium(index=1)

waveguide_width = 0.5
design_region_width = 2.5
design_region_height = 2.5
arm_seperation = 1.0
waveguide_length = 0.5
pml_size = 1
resolution = 20 # pixels/micrometer

minimum_length = 0.09
eta_e = 0.75
filter_radius = mpa.get_conic_radius_from_eta_e(minimum_length, eta_e)
eta_i = 0.5
eta_d = 1-eta_e
design_region_resolution = int(4*resolution)
frequencies = 1/np.linspace(1.5, 1.6, 5)

Nx = int((design_region_resolution*design_region_width)/10)  
Ny = int((design_region_resolution*design_region_height)/10) 

design_variables = mp.MaterialGrid(mp.Vector3(Nx, Ny), air, Si)
design_region = mpa.DesignRegion(design_variables, volume=mp.Volume(
    center=mp.Vector3(), size=mp.Vector3(design_region_width, design_region_height)))

# Simulation

Sx = 2*pml_size + 2*waveguide_length + design_region_width  # 5.5
Sy = 2*pml_size + design_region_height + 0.5              # 5
cell_size = mp.Vector3(Sx, Sy)



pml_layers = [mp.PML(pml_size)]


fwidth = 0.1
fcen = 1/1.55

source_center = [-Sx/2.3 + pml_size - waveguide_length/3, 0, 0]
source_size = mp.Vector3(0, 0.75, 0)
kpoint = mp.Vector3(1, 0, 0)
src = mp.GaussianSource(frequency=fcen, fwidth=fwidth)
source = [mp.EigenModeSource(src, eig_band=1, direction=mp.NO_DIRECTION,
                             eig_kpoint=kpoint, size=source_size, center=source_center)]
geometry = [
    mp.Block(
        center=mp.Vector3(x=-Sx/4), material=Si,
    size=mp.Vector3(9, waveguide_width, 0))]

sim = mp.Simulation(cell_size=cell_size,
                    boundary_layers=pml_layers,
                    geometry=geometry,
                    sources=source,
                    resolution=resolution
                    )

sim.plot2D()
plt.show()

nfreq = 1 

 # reflected flux
refl_fr = mp.FluxRegion(
     center=mp.Vector3(-1.45, 0, 0), size=mp.Vector3(0, 0.75, 0)
 )
refl = sim.add_flux(fcen, fwidth, nfreq, refl_fr)

# transmitted flux
tran_fr = mp.FluxRegion(
    center=mp.Vector3(1.75, 0, 0), size=mp.Vector3(0, 0.75, 0)
)
tran = sim.add_flux(fcen, fwidth, nfreq, tran_fr)

sim.plot2D()
plt.show()

pt = mp.Vector3(1.75, 0.25)

sim.run(until_after_sources=mp.stop_when_fields_decayed(0.1, mp.Ez, pt, 1e-3))

# for normalization run, save flux fields data for reflection plane
straight_refl_data = sim.get_flux_data(refl)


print("RS=",straight_refl_data )

# save incident power for transmission plane
straight_tran_flux = mp.get_fluxes(tran)

print("T=",straight_tran_flux )

sim.reset_meep()

geometry = [
    mp.Block(center=mp.Vector3(x=-Sx/4), material=Si,
             size=mp.Vector3(Sx/2+1, waveguide_width, 0)),
    mp.Block(center=mp.Vector3(x=Sx/4, y=arm_seperation/2),
             material=Si, size=mp.Vector3(Sx/2+1, waveguide_width, 0)),
    mp.Block(center=mp.Vector3(x=Sx/4, y=-arm_seperation/2),
             material=Si, size=mp.Vector3(Sx/2+1, waveguide_width, 0)),
    mp.Block(center=design_region.center,
              size=design_region.size, material=design_variables)
]


count = 0
number = 0
number_iteration = 75000
desen_data = []
input_datas_for_desen = []
input_data_all_for_desen = []

file_path_desen = '/home/sengor/Inverse_design_files/pattern_data_symmetric.npy'     #replace with your file location
file_path_optic = '/home/sengor/Inverse_design_files/optic_data_symmetric.npy'       #replace with your file location

for i in range(number_iteration):     ##### random symmetric pattern data generaion

    # desen = np.random.randint(2, size=(Nx, Ny))
    desen = np.random.randint(2,size=(Nx,int(Ny/2)))
    desen = np.hstack((desen,desen[:,::-1]))
    # plt.imshow(desen, cmap="gray")
    # plt.show()
    # plt.imshow(np.rot90(desen, k=1), cmap="gray")
    # plt.show()
    

 
# desen = desen.reshape((Nx,Ny), order="F")

    
    design_region.update_design_parameters(desen)
    
    
    sim = mp.Simulation(cell_size=cell_size,
                        boundary_layers=pml_layers,
                        geometry=geometry,
                        sources=source,
                        default_material=air,
                        resolution=resolution)
    
    # reflected flux
    refl = sim.add_flux(fcen, fwidth, nfreq, refl_fr)
    
    # transmitted flux1
    tran_fr1 = mp.FluxRegion(
        center=mp.Vector3(1.5, 0.5, 0), size=mp.Vector3(0, 0.75, 0)
    )
    tran1 = sim.add_flux(fcen, fwidth, nfreq, tran_fr1)
    
     # transmitted flux2
    tran_fr2 = mp.FluxRegion(
         center=mp.Vector3(1.5, -0.5, 0), size=mp.Vector3(0, 0.75, 0)
     )
    tran2 = sim.add_flux(fcen, fwidth, nfreq, tran_fr2)
    
    
    # for normal run, load negated fields to subtract incident from refl. fields
    sim.load_minus_flux_data(refl, straight_refl_data)
    
    pt = mp.Vector3(1.5, 0.5)
    
    sim.run(until_after_sources=mp.stop_when_fields_decayed(0.1, mp.Ez, pt, 1e-3))
    
    tran_flux1 = mp.get_fluxes(tran1)
    tran_flux2 = mp.get_fluxes(tran2)
    refl_flux = mp.get_fluxes(refl)
    
    flux_freqs = mp.get_flux_freqs(refl)
    
    fwave_length = 1/flux_freqs[0]
       
    sim.plot2D()
    plt.show()
    
    count = count + 1;
    print("count=",count)
    
    
        
    Rs =  -np.array(refl_flux) / np.array(straight_tran_flux)
    Ts1 = np.array(tran_flux1)  / np.array(straight_tran_flux)
    Ts2 = np.array(tran_flux2) / np.array(straight_tran_flux)      
    Ls = (1- Rs - Ts1- Ts2)
    print("Rs=" ,Rs, "Ts1=", Ts1, "Ts2=", Ts2, "Ls=", Ls)
    
    if Ts1 >=0.35 and Ts2 >=0.35:
       print("Rs=" ,Rs, "Ts1=", Ts1, "Ts2=", Ts2, "Ls=", Ls)
       number = number + 1
       print("number=", number)
       desen_data.append(desen)
       np.save(file_path_desen, desen_data)
       input_datas_for_desen = np.column_stack((Rs, Ts1, Ts2))
       input_data_all_for_desen.append(input_datas_for_desen)
    
    
   
np.save(file_path_optic,input_data_all_for_desen)    


#######
# print(input_data_all_for_desen[0])
# print(desen_data[0])

# # Assuming "desen_data[0]" is your NumPy array
# image = desen_data[2]
# plt.imshow(image, cmap="gray")
# plt.show()

# # Calculate the width of the image and the split point
# width = image.shape[1]
# split_column = width // 2

# # Create a new array for the symmetric image
# symmetric_image = np.copy(image)

# # Cancel out the left half
# symmetric_image[:, :split_column] = 0

# # Copy the right half to the left half as a column
# symmetric_image[:, :split_column] = symmetric_image[:, split_column:]

# # Flip the right half horizontally and copy it to the left half
# symmetric_image[:, :split_column] = np.flip(symmetric_image[:, :split_column], axis=1)
# # print(symmetric_image)
# plt.imshow(symmetric_image, cmap="gray")
# plt.show()

######################################################################
######################################################################

input_data_all_for_ayiklanmis_desen = []
ayiklanmis_fake_images = []

file_path_ayiklanmis_optic = '/home/sengor/Inverse_design_files/ayiklanmis_optic_data_20x20_>90_asymmetric.npy'                #replace with your file 
file_path_ayiklanmis_fake_images = '/home/sengor/Inverse_design_files/ayiklanmis_fake_images_data_20x20_>90_asymmetric.npy'    #replace with your file 
precision = 8
different = 0
counter = 0
# input_datas_for_fake_images = []
# file_path_shuffled_fake_images = '/home/sengor/Inverse_design_files/shuffled_fake_images.npy'
# file_path_input_data_for_fake_images = '/home/sengor/Inverse_design_files/input_datas_for_fake_images.npy'
# Initialize an empty set to store unique data
# input_data_all_for_ayiklanmis_desen = set()

fake_images = np.load("v_prediction_images.npy")


for i in range(fake_images.shape[0]):
    sim.reset_meep()
    design_region.update_design_parameters(fake_images[i])
    
    
    sim = mp.Simulation(cell_size=cell_size,
                        boundary_layers=pml_layers,
                        geometry=geometry,
                        sources=source,
                        default_material=air,
                        resolution=resolution)
    
    # reflected flux
    refl = sim.add_flux(fcen, fwidth, nfreq, refl_fr)
    
    # transmitted flux1
    tran_fr1 = mp.FluxRegion(
        center=mp.Vector3(1.5, 0.5, 0), size=mp.Vector3(0, 0.75, 0)
    )
    tran1 = sim.add_flux(fcen, fwidth, nfreq, tran_fr1)
    
     # transmitted flux2
    tran_fr2 = mp.FluxRegion(
         center=mp.Vector3(1.5, -0.5, 0), size=mp.Vector3(0, 0.75, 0)
     )
    tran2 = sim.add_flux(fcen, fwidth, nfreq, tran_fr2)
    
    
    # for normal run, load negated fields to subtract incident from refl. fields
    sim.load_minus_flux_data(refl, straight_refl_data)
    
    pt = mp.Vector3(1.5, 0.5)
    
    sim.run(until_after_sources=mp.stop_when_fields_decayed(0.1, mp.Ez, pt, 1e-3))
    
    tran_flux1 = mp.get_fluxes(tran1)
    tran_flux2 = mp.get_fluxes(tran2)
    refl_flux = mp.get_fluxes(refl)
    
    flux_freqs = mp.get_flux_freqs(refl)
    
    fwave_length = 1/flux_freqs[0]
       
    # sim.plot2D()
    # plt.show()
    
    
    
    
        
    Rs =  -np.array(refl_flux) / np.array(straight_tran_flux)
    Ts1 = np.array(tran_flux1)  / np.array(straight_tran_flux)
    Ts2 = np.array(tran_flux2) / np.array(straight_tran_flux)      
    Ls = (1- Rs - Ts1- Ts2)
    sim.plot2D()
    plt.show()
    
    rounded_data = np.round(np.column_stack((Rs, Ts1, Ts2)), precision)

    if Ts1 + Ts2 >= 0.9:
     
        counter = counter + 1
        print("counter=",counter)
        
        ### use here for selected_pattern
        
        if rounded_data.tolist() not in input_data_all_for_ayiklanmis_desen:
             input_data_all_for_ayiklanmis_desen.append(rounded_data.tolist())
             np.save(file_path_ayiklanmis_optic, input_data_all_for_ayiklanmis_desen)
    
        
             ayiklanmis_fake_images.append(fake_images[i])
             np.save(file_path_ayiklanmis_fake_images, ayiklanmis_fake_images)
             different = different + 1
             print("different =",different)
        
    
    print("Rs=" ,Rs, "Ts1=", Ts1, "Ts2=", Ts2, "Ls=", Ls)
    input_datas_for_fake_images.append(np.column_stack((Rs, Ts1, Ts2)))
    np.save(file_path_input_data_for_fake_images,input_datas_for_fake_images)
