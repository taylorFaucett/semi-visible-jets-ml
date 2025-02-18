import uproot
import numpy as np
import glob
import os
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import trange, tqdm
from numpy.lib.recfunctions import append_fields
from matplotlib import rcParams
from pyjet import cluster
from pyjet.testdata import get_event

home = os.getcwd()

rcParams["font.family"] = "serif"
plt.rcParams.update({"font.size": 12})


def struc2arr(x):
    # pyjet outputs a structured array. This converts
    # the 4 component structured array into a simple
    # 4xN numpy array
    x = x.view((float, len(x.dtype.names)))
    return x


def calc_minv(j1, j2):
    pt1 = j1["Jet.PT"]
    pt2 = j2["Jet.PT"]
    dEta = j1["Jet.Eta"] - j2["Jet.Eta"]
    dPhi = j1["Jet.Phi"] - j2["Jet.Phi"]
    minv = np.sqrt(2.0 * pt1 * pt2 * (np.cosh(dEta) - np.cos(dPhi)))
    return minv


def jet_minv(jets):
    minvs = []
    for idx, entry in jets.groupby("entry"):
        j1 = entry.iloc[0]
        j2 = entry.iloc[1]
        minv = calc_minv(j1, j2)
        minvs.append(minv)
    return minvs


def Mjj_plot(X, label):
    lb, ub, n_bins = 7e2, 1e4, 150
    plt.figure(figsize=(8, 6))
    bins = np.linspace(lb, ub, n_bins)
    plt.hist(X, bins=bins, histtype="step", label=label, linewidth=3)
    plt.yscale("log")
    plt.xscale("log")
    plt.xlim([lb, ub])
    plt.ylim([1e0, 5e6])
    plt.text(2.6e3, 4e-1, "$3\\times10^3$")
    plt.xlabel("$M_{jj} [GeV]$")
    plt.ylabel("Events")
    plt.legend()
    plt.title("N = " + str(len(X)))
    plt_path = os.path.join(home, "svj-production", "analysis", "figures", "Mjj.png")
    plt.savefig(plt_path)


def trim_jets(jets, pt1_cut, pt2_cut, abs_eta_cut):
    for idx, entry in jets.groupby("entry"):
        # Gaurantee we have at least 2 jets
        if len(entry) < 2:
            jets = jets.drop(idx, level="entry")
        else:
            # If we have more than 2 jets, drop events which fail our cuts on pT and |eta|
            j1 = entry.iloc[0]
            j2 = entry.iloc[1]
            abs_eta = np.absolute(j1["Jet.Eta"] - j2["Jet.Eta"])
            if (
                j1["Jet.PT"] < pt1_cut
                or j2["Jet.PT"] < pt2_cut
                or abs_eta >= abs_eta_cut
            ):
                jets = jets.drop(idx, level="entry")
    return jets


def jets_2_image(jets, R0, R1, ptmin):
    # R0 = Clustering radius for the main jets
    # R1 = Clustering radius for the subjets in the primary jet
    for event in jets.groupby("entry"):
        trim_pt, trim_eta, trim_phi, trim_mass = [], [], [], []

        # Convert event to a pyjet compatible format
        # Convert to float64
        event = event.astype(np.float64)

        # Convert the pandas dataframe to a structured array
        # (pT, eta, phi, mass)
        event = event.to_records(index=False)

        # Convert to a structured array (for pyjet)
        sequence = cluster(event, R=R0, p=-1)
        jets = sequence.inclusive_jets(ptmin=ptmin)

        # Main jets
        jets = sequence.inclusive_jets(ptmin=3)

        # # In case we are missing a leading jet, break early
        # if len(jets) == 0:
        #     return cut_fail()

        # Take just the leading jet
        jet0 = jets[0]

        # Define a cut threshold that the subjets have to meet (i.e. 5% of the original jet pT)
        jet0_max = jet0.pt
        jet0_cut = jet0_max * 0.05

        # Grab the subjets by clustering with R1
        subjets = cluster(jet0.constituents_array(), R=R1, p=1)
        subjet_array = subjets.inclusive_jets()
        for subjet in subjet_array:
            if subjet.pt > jet0_cut:
                # Get the subjets pt, eta, phi constituents
                subjet_data = subjet.constituents_array()
                print(subjet_data)
                exit()
                subjet_data = struc2arr(subjet_data)
                pT = subjet_data[:, 0]
                eta = subjet_data[:, 1]
                phi = subjet_data[:, 2]
                mass = subjet_data[:, 3]

                # Shift all data such that the leading subjet
                # is located at (eta,phi) = (0,0)
                eta -= subjet_array[0].eta
                phi -= subjet_array[0].phi

                # Rotate the jet image such that the second leading
                # jet is located at -pi/2
                # s1x, s1y = subjet_array[1].eta, subjet_array[1].phi
                # theta = np.arctan2(s1y, s1x)
                # if theta < 0.0:
                #     theta += 2 * np.pi
                # eta, phi = rotate(eta, phi, np.pi - theta)

                # Collect the trimmed subjet constituents
                trim_pt.append(pT)
                trim_eta.append(eta)
                trim_phi.append(phi)
                trim_mass.append(mass)
        print(trim_pt)
        # jet_images = jet_images.append(dfi, ignore_index=True)
        # print(jet_images)


def run_data(rinv, calc_minv, calc_jet_img):
    rinv_path = os.path.join(home, "svj-production", "pt_eta_phi_mass", rinv, "*.h5")
    files = glob.glob(rinv_path)
    combined_minv = []

    for file in tqdm(files):
        # Load raw [pt, eta, phi, mass] data
        jets = pd.read_hdf(file, "df")

        # get run_file details
        run_name = os.path.basename(file)
        trim_file = os.path.join(
            home, "svj-production", "trimmed_pt_eta_phi_mass", rinv, run_name
        )

        # Trim raw jet data for pt cuts
        # This process is slower than most, so the results are stored and re-loaded
        # rather than re-calculated each time
        if not os.path.isfile(trim_file):
            # Trim jets
            trimmed_jets = trim_jets(jets, pt1_cut=440, pt2_cut=60, abs_eta_cut=1.2)
            trimmed_jets.to_hdf(trim_file, "df")
        else:
            # Jets already trimmed. Load trimmed jet from file
            trimmed_jets = pd.read_hdf(trim_file, "df")

        if calc_minv:
            # Calculate invariant masses from the trimmed constituents
            minvs = jet_minv(trimmed_jets)
            combined_minv.extend(minvs)

            # Plot the results
            Mjj_plot(X=combined_minv, label=rinv)

        if calc_jet_img:
            jets_2_image(trimmed_jets, R0=1.0, R1=0.3, ptmin=3)


if __name__ == "__main__":
    rinvs = ["0p0", "0p3", "1p0"]
    for rinv in rinvs:
        run_data(rinv, calc_minv=False, calc_jet_img=True)
