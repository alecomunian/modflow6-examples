# ## One-Dimensional Transport in a Uniform Flow Field Comparison of MODFLOW 6 transport with MT3DMS
#
# The purpose of this script is to (1) recreate the example problems that were first
# described in the 1999 MT3DMS report, and (2) compare MODFLOW 6-GWT solutions to the
# established MT3DMS solutions.
#
# Ten example problems appear in the 1999 MT3DMS manual, starting on page 130.
# This notebook demonstrates example 1 from the list below:
#
#   1.  *One-Dimensional Transport in a Uniform Flow Field*,
#   2.  One-Dimensional Transport with Nonlinear or Nonequilibrium Sorption,
#   3.  Two-Dimensional Transport in a Uniform Flow Field,
#   4.  Two-Dimensional Transport in a Diagonal Flow Field,
#   5.  Two-Dimensional Transport in a Radial Flow Field,
#   6.  Concentration at an Injection/Extraction Well,
#   7.  Three-Dimensional Transport in a Uniform Flow Field,
#   8.  Two-Dimensional, Vertical Transport in a Heterogeneous Aquifer,
#   9.  Two-Dimensional Application Example, and
#   10. Three-Dimensional Field Case Study.
#

# ### MODFLOW 6 GWT MT3DMS Example 1 Problem Setup

# Imports

import os
import sys
import matplotlib.pyplot as plt
import flopy
import numpy as np

# Append to system path to include the common subdirectory

sys.path.append(os.path.join("..", "common"))

# Import common functionality

import config
from figspecs import USGSFigure

mf6exe = os.path.abspath(config.mf6_exe)
exe_name_mf = config.mf2005_exe
exe_name_mt = config.mt3dms_exe

# Set figure properties specific to this problem

figure_size = (5, 3.5)

# Base simulation and model name and workspace

ws = config.base_ws

# Set scenario parameters (make sure there is at least one blank line before next item)
# This entire dictionary is passed to _build_model()_ using the kwargs argument

parameters = {
    "ex-gwt-mt3dms-p01a": {
        "dispersivity": 0.0,
        "retardation": 1.0,
        "decay": 0.0,
    },
    "ex-gwt-mt3dms-p01b": {
        "dispersivity": 10.0,
        "retardation": 1.0,
        "decay": 0.0,
    },
    "ex-gwt-mt3dms-p01c": {
        "dispersivity": 10.0,
        "retardation": 5.0,
        "decay": 0.0,
    },
    "ex-gwt-mt3dms-p01d": {
        "dispersivity": 10.0,
        "retardation": 5.0,
        "decay": 0.002,
    },
}

# Scenario parameter units
#
# add parameter_units to add units to the scenario parameter table that is automatically
# built and used by the .tex input

parameter_units = {
    "dispersivity": "$m$",
    "retardation": "unitless",
    "decay": "$d^{-1}$",
}

# Model units

length_units = "meters"
time_units = "days"

# Table MODFLOW 6 GWT MT3DMS Example 1

nper = 1  # Number of periods
nlay = 1  # Number of layers
ncol = 101  # Number of columns
nrow = 1  # Number of rows
delr = 10.0  # Column width ($m$)
delc = 1.0  # Row width ($m$)
top = 0.0  # Top of the model ($m$)
botm = -1.0  # Layer bottom elevations ($m$)
prsity = 0.25  # Porosity
perlen = 2000  # Simulation time ($days$)
k11 = 1.0  # Horizontal hydraulic conductivity ($m/d$)

# Set some static model parameter values

k33 = k11  # Vertical hydraulic conductivity ($m/d$)
laytyp = 1
nstp = 100.0
dt0 = perlen / nstp
Lx = (ncol - 1) * delr
v = 0.24
q = v * prsity
h1 = q * Lx
strt = np.zeros((nlay, nrow, ncol), dtype=float)
strt[0, 0, 0] = h1  # Starting head ($m$)
l = 1000.0  # Needed for plots
icelltype = 1  # Cell conversion type
ibound = np.ones((nlay, nrow, ncol), dtype=int)
ibound[0, 0, 0] = -1
ibound[0, 0, -1] = -1

# Set some static transport related model parameter values

mixelm = 0  # TVD
rhob = 0.25
sp2 = 0.0  # red, but not used in this problem
sconc = np.zeros((nlay, nrow, ncol), dtype=float)
dmcoef = 0.0  # Molecular diffusion coefficient

# Set solver parameter values (and related)
nouter, ninner = 100, 300
hclose, rclose, relax = 1e-6, 1e-6, 1.0
ttsmult = 1.0
dceps = 1.0e-5  # HMOC parameters in case they are invoked
nplane = 1  # HMOC
npl = 0  # HMOC
nph = 4  # HMOC
npmin = 0  # HMOC
npmax = 8  # HMOC
nlsink = nplane  # HMOC
npsink = nph  # HMOC

# Static temporal data used by TDIS file

tdis_rc = []
tdis_rc.append((perlen, nstp, 1.0))

# ### Create MODFLOW 6 GWT MT3DMS Example 1 Boundary Conditions
#
# Constant head cells are specified on both ends of the model

chdspd = [[(0, 0, 0), h1], [(0, 0, ncol - 1), 0.0]]
c0 = 1.0
cncspd = [[(0, 0, 0), c0]]


# ### Functions to build, write, run, and plot MODFLOW 6 GWT MT3DMS Example 1 model results
#
# MODFLOW 6 flopy simulation object (sim) is returned if building the model


def build_model(
    sim_name,
    dispersivity=0.0,
    retardation=0.0,
    decay=0.0,
    mixelm=0,
    silent=False,
):
    if config.buildModel:

        mt3d_ws = os.path.join(ws, sim_name, "mt3d")
        modelname_mf = "p01-mf"

        # Instantiate the MODFLOW model
        mf = flopy.modflow.Modflow(
            modelname=modelname_mf, model_ws=mt3d_ws, exe_name=exe_name_mf
        )

        # Instantiate discretization package
        # units: itmuni=4 (days), lenuni=2 (m)
        flopy.modflow.ModflowDis(
            mf,
            nlay=nlay,
            nrow=nrow,
            ncol=ncol,
            delr=delr,
            delc=delc,
            top=top,
            nstp=nstp,
            botm=botm,
            perlen=perlen,
            itmuni=4,
            lenuni=2,
        )

        # Instantiate basic package
        flopy.modflow.ModflowBas(mf, ibound=ibound, strt=strt)

        # Instantiate layer property flow package
        flopy.modflow.ModflowLpf(mf, hk=k11, laytyp=laytyp)

        # Instantiate solver package
        flopy.modflow.ModflowPcg(mf)

        # Instantiate link mass transport package (for writing linker file)
        flopy.modflow.ModflowLmt(mf)

        # Transport
        modelname_mt = "p01-mt"
        mt = flopy.mt3d.Mt3dms(
            modelname=modelname_mt,
            model_ws=mt3d_ws,
            exe_name=exe_name_mt,
            modflowmodel=mf,
        )

        c0 = 1.0
        icbund = np.ones((nlay, nrow, ncol), dtype=int)
        icbund[0, 0, 0] = -1
        sconc = np.zeros((nlay, nrow, ncol), dtype=float)
        sconc[0, 0, 0] = c0
        flopy.mt3d.Mt3dBtn(
            mt,
            laycon=laytyp,
            icbund=icbund,
            prsity=prsity,
            sconc=sconc,
            dt0=dt0,
            ifmtcn=1,
        )

        # Instatiate the advection package
        flopy.mt3d.Mt3dAdv(
            mt,
            mixelm=mixelm,
            dceps=dceps,
            nplane=nplane,
            npl=npl,
            nph=nph,
            npmin=npmin,
            npmax=npmax,
            nlsink=nlsink,
            npsink=npsink,
            percel=0.5,
        )

        # Instantiate the dispersion package
        flopy.mt3d.Mt3dDsp(mt, al=dispersivity)

        # Set reactive variables and instantiate chemical reaction package
        if retardation == 1.0:
            isothm = 0.0
            rc1 = 0.0
        else:
            isothm = 1
        if decay != 0:
            ireact = 1
            rc1 = decay
        else:
            ireact = 0.0
            rc1 = 0.0
        kd = (retardation - 1.0) * prsity / rhob
        flopy.mt3d.Mt3dRct(
            mt,
            isothm=isothm,
            ireact=ireact,
            igetsc=0,
            rhob=rhob,
            sp1=kd,
            rc1=rc1,
            rc2=rc1,
        )

        # Instantiate the source/sink mixing package
        flopy.mt3d.Mt3dSsm(mt)

        # Instantiate the GCG solver in MT3DMS
        flopy.mt3d.Mt3dGcg(mt, mxiter=10)

        # MODFLOW 6
        name = "p01-mf6"
        gwfname = "gwf-" + name
        sim_ws = os.path.join(ws, sim_name)
        sim = flopy.mf6.MFSimulation(
            sim_name=sim_name, sim_ws=sim_ws, exe_name=mf6exe
        )

        # Instantiating MODFLOW 6 time discretization
        flopy.mf6.ModflowTdis(
            sim, nper=nper, perioddata=tdis_rc, time_units=time_units
        )

        # Instantiating MODFLOW 6 groundwater flow model
        gwf = flopy.mf6.ModflowGwf(
            sim,
            modelname=gwfname,
            save_flows=True,
            model_nam_file="{}.nam".format(gwfname),
        )

        # Instantiating MODFLOW 6 solver for flow model
        imsgwf = flopy.mf6.ModflowIms(
            sim,
            print_option="SUMMARY",
            outer_dvclose=hclose,
            outer_maximum=nouter,
            under_relaxation="NONE",
            inner_maximum=ninner,
            inner_dvclose=hclose,
            rcloserecord=rclose,
            linear_acceleration="CG",
            scaling_method="NONE",
            reordering_method="NONE",
            relaxation_factor=relax,
            filename="{}.ims".format(gwfname),
        )
        sim.register_ims_package(imsgwf, [gwf.name])

        # Instantiating MODFLOW 6 discretization package
        flopy.mf6.ModflowGwfdis(
            gwf,
            length_units=length_units,
            nlay=nlay,
            nrow=nrow,
            ncol=ncol,
            delr=delr,
            delc=delc,
            top=top,
            botm=botm,
            idomain=np.ones((nlay, nrow, ncol), dtype=int),
            filename="{}.dis".format(gwfname),
        )

        # Instantiating MODFLOW 6 node-property flow package
        flopy.mf6.ModflowGwfnpf(
            gwf,
            save_flows=False,
            icelltype=icelltype,
            k=k11,
            k33=k33,
            save_specific_discharge=True,
            filename="{}.npf".format(gwfname),
        )

        # Instantiating MODFLOW 6 initial conditions package for flow model
        flopy.mf6.ModflowGwfic(
            gwf, strt=strt, filename="{}.ic".format(gwfname)
        )

        # Instantiating MODFLOW 6 constant head package
        flopy.mf6.ModflowGwfchd(
            gwf,
            maxbound=len(chdspd),
            stress_period_data=chdspd,
            save_flows=False,
            pname="CHD-1",
            filename="{}.chd".format(gwfname),
        )

        # Instantiating MODFLOW 6 output control package for flow model
        flopy.mf6.ModflowGwfoc(
            gwf,
            head_filerecord="{}.hds".format(gwfname),
            budget_filerecord="{}.cbc".format(gwfname),
            headprintrecord=[
                ("COLUMNS", 10, "WIDTH", 15, "DIGITS", 6, "GENERAL")
            ],
            saverecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
            printrecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
        )

        # Instantiating MODFLOW 6 groundwater transport package
        gwtname = "gwt-" + name
        gwt = flopy.mf6.MFModel(
            sim,
            model_type="gwt6",
            modelname=gwtname,
            model_nam_file="{}.nam".format(gwtname),
        )
        gwt.name_file.save_flows = True
        imsgwt = flopy.mf6.ModflowIms(
            sim,
            print_option="SUMMARY",
            outer_dvclose=hclose,
            outer_maximum=nouter,
            under_relaxation="NONE",
            inner_maximum=ninner,
            inner_dvclose=hclose,
            rcloserecord=rclose,
            linear_acceleration="BICGSTAB",
            scaling_method="NONE",
            reordering_method="NONE",
            relaxation_factor=relax,
            filename="{}.ims".format(gwtname),
        )
        sim.register_ims_package(imsgwt, [gwt.name])

        # Instantiating MODFLOW 6 transport discretization package
        flopy.mf6.ModflowGwtdis(
            gwt,
            nlay=nlay,
            nrow=nrow,
            ncol=ncol,
            delr=delr,
            delc=delc,
            top=top,
            botm=botm,
            idomain=1,
            filename="{}.dis".format(gwtname),
        )

        # Instantiating MODFLOW 6 transport initial concentrations
        flopy.mf6.ModflowGwtic(
            gwt, strt=sconc, filename="{}.ic".format(gwtname)
        )

        # Instantiating MODFLOW 6 transport advection package
        if mixelm == 0:
            scheme = "UPSTREAM"
        elif mixelm == -1:
            scheme = "TVD"
        else:
            raise Exception()
        flopy.mf6.ModflowGwtadv(
            gwt, scheme=scheme, filename="{}.adv".format(gwtname)
        )

        # Instantiating MODFLOW 6 transport dispersion package
        if dispersivity != 0:
            flopy.mf6.ModflowGwtdsp(
                gwt,
                xt3d_off=True,
                alh=dispersivity,
                ath1=dispersivity,
                filename="{}.dsp".format(gwtname),
            )

        # Instantiating MODFLOW 6 transport mass storage package (formerly "reaction" package in MT3DMS)
        if retardation != 1.0:
            sorption = "linear"
            kd = (
                (retardation - 1.0) * prsity / rhob
            )  # prsity & rhob defined in
        else:  # global variable section
            sorption = None
            kd = 1.0
        if decay != 0.0:
            first_order_decay = True
        else:
            first_order_decay = False
        flopy.mf6.ModflowGwtmst(
            gwt,
            porosity=prsity,
            sorption=sorption,
            bulk_density=rhob,
            distcoef=kd,
            first_order_decay=first_order_decay,
            decay=decay,
            decay_sorbed=decay,
            filename="{}.mst".format(gwtname),
        )

        # Instantiating MODFLOW 6 transport constant concentration package
        flopy.mf6.ModflowGwtcnc(
            gwt,
            maxbound=len(cncspd),
            stress_period_data=cncspd,
            save_flows=False,
            pname="CNC-1",
            filename="{}.cnc".format(gwtname),
        )

        # Instantiating MODFLOW 6 transport source-sink mixing package
        flopy.mf6.ModflowGwtssm(
            gwt, sources=[[]], filename="{}.ssm".format(gwtname)
        )

        # Instantiating MODFLOW 6 transport output control package
        flopy.mf6.ModflowGwtoc(
            gwt,
            budget_filerecord="{}.cbc".format(gwtname),
            concentration_filerecord="{}.ucn".format(gwtname),
            concentrationprintrecord=[
                ("COLUMNS", 10, "WIDTH", 15, "DIGITS", 6, "GENERAL")
            ],
            saverecord=[("CONCENTRATION", "LAST"), ("BUDGET", "LAST")],
            printrecord=[("CONCENTRATION", "LAST"), ("BUDGET", "LAST")],
        )

        # Instantiating MODFLOW 6 flow-transport exchange mechanism
        flopy.mf6.ModflowGwfgwt(
            sim,
            exgtype="GWF6-GWT6",
            exgmnamea=gwfname,
            exgmnameb=gwtname,
            filename="{}.gwfgwt".format(name),
        )
        return mf, mt, sim
    return None


# Function to write model files


def write_model(mf2k5, mt3d, sim, silent=True):
    if config.writeModel:
        mf2k5.write_input()
        mt3d.write_input()
        sim.write_simulation(silent=silent)


# Function to run the models.
# _True_ is returned if the model runs successfully


@config.timeit
def run_model(mf2k5, mt3d, sim, silent=True):
    success = True
    if config.runModel:
        success, buff = mf2k5.run_model(silent=silent)
        success, buff = mt3d.run_model(silent=silent)
        success, buff = sim.run_simulation(silent=silent)
        if not success:
            print(buff)
    return success


# Function to plot the model results


def plot_results(mt3d, mf6, idx, ax=None):
    if config.plotModel:
        mt3d_out_path = mt3d.model_ws
        mf6_out_path = mf6.simulation_data.mfpath.get_sim_path()
        mf6.simulation_data.mfpath.get_sim_path()

        # Get the MT3DMS concentration output
        fname_mt3d = os.path.join(mt3d_out_path, "MT3D001.UCN")
        ucnobj_mt3d = flopy.utils.UcnFile(fname_mt3d)
        conc_mt3d = ucnobj_mt3d.get_alldata()

        # Get the MF6 concentration output
        gwt = mf6.get_model(list(mf6.model_names)[1])
        ucnobj_mf6 = gwt.output.concentration()
        conc_mf6 = ucnobj_mf6.get_alldata()

        # Create figure for scenario
        fs = USGSFigure(figure_type="graph", verbose=False)
        sim_name = mf6.name
        if ax is None:
            fig, ax = plt.subplots(
                1, 1, figsize=figure_size, dpi=300, tight_layout=True
            )

        ax.plot(
            np.linspace(0, l, ncol),
            conc_mt3d[0, 0, 0, :],
            color="k",
            label="MT3DMS",
            linewidth=0.5,
        )
        ax.plot(
            np.linspace(0, l, ncol),
            conc_mf6[0, 0, 0, :],
            "^",
            markeredgewidth=0.5,
            color="blue",
            fillstyle="none",
            label="MF6",
            markersize=3,
        )
        ax.set_ylim(0, 1.2)
        ax.set_xlim(0, 1000)
        ax.set_xlabel("Distance, in m")
        ax.set_ylabel("Concentration")
        title = "Concentration Profile at Time = 2,000 " + "{}".format(
            time_units
        )
        ax.legend()
        letter = chr(ord("@") + idx + 1)
        fs.heading(letter=letter, heading=title)

        # save figure
        if config.plotSave:
            fpth = os.path.join(
                "..", "figures", "{}{}".format(sim_name, config.figure_ext)
            )
            fig.savefig(fpth)


# Function that wraps all of the steps for each scenario.
#
# 1. build_model,
# 2. write_model,
# 3. run_model, and
# 4. plot_results.


def scenario(idx, silent=True):
    key = list(parameters.keys())[idx]
    parameter_dict = parameters[key]
    mf2k5, mt3d, sim = build_model(key, **parameter_dict)

    write_model(mf2k5, mt3d, sim, silent=silent)

    success = run_model(mf2k5, mt3d, sim, silent=silent)

    if success:
        plot_results(mt3d, sim, idx)


# nosetest - exclude block from this nosetest to the next nosetest
def test_01():
    scenario(0, silent=False)


def test_02():
    scenario(1, silent=False)


def test_03():
    scenario(2, silent=False)


def test_04():
    scenario(3, silent=False)


# nosetest end

if __name__ == "__main__":
    # ### Advection only

    scenario(0)

    # ### Advection and dispersion

    scenario(1)

    # ### Advection, dispersion, and retardation

    scenario(2)

    # ### Advection, dispersion, retardation, and decay

    scenario(3)
