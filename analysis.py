# Authors: Devon Callan, Shivani Medhan
# June 2025

import os
from typing import Optional, Dict, Tuple

import pandas as pd

#################
### Constants ###
#################

TIME_KEY = "Time [min]"

CONC_KEY_FORMAT = "Concentration {} [mol/L]"
CONV_KEY_FORMAT = "Conversion {} [%]"

CONC_KEY = "Concentration [mol/L]"
CONV_KEY = "Conversion [%]"

UV_VIS_KEY = "UV_Vis"
IR_KEY = "IR"
NMR_KEY = "NMR"
INSTRUMENT_KEYS = [UV_VIS_KEY, IR_KEY, NMR_KEY]

COLORS = {
    UV_VIS_KEY: "tab:blue",
    IR_KEY: "tab:green",
    NMR_KEY: "tab:red",
}


default_wavelength_map = {
    1: 330,
    2: 350,
    3: 370,
    4: 390,
}


###############################
### Read and Parse Raw Data ###
###############################


def read_UV_Vis_data(
    data_dir: str,
    sample_name: str,
    wavelength_map: dict = default_wavelength_map,
    init_conc: Optional[float] = 1.0,
    abs_coeff: Optional[float] = None,
) -> Optional[pd.DataFrame]:

    data_path = f"{data_dir}/UV-Vis/{sample_name}"

    try:
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        elif not os.path.exists(data_path):
            raise FileNotFoundError(f"UV-Vis data file not found: {data_path}")
    except FileNotFoundError as e:
        print(e)
        return None

    data = pd.read_csv(data_path, delimiter=",", skipinitialspace=True)

    cols = ["Time"] + [f"UV/Vis {i}" for i in wavelength_map.keys()]

    df_extracted = data[cols].copy()
    df_extracted.columns = [TIME_KEY] + [
        f"UV-Vis [{w} nm]" for w in wavelength_map.values()
    ]

    for i, w in wavelength_map.items():

        conc_key = CONC_KEY_FORMAT.format(i)
        conv_key = CONV_KEY_FORMAT.format(i)

        if abs_coeff is not None:
            # Calculate concentration using the provided absorbance coefficient
            df_extracted[conc_key] = df_extracted[f"UV-Vis [{w} nm]"].apply(
                lambda x: x / abs_coeff if abs_coeff != 0 else 0
            )
            df_extracted[conc_key] = df_extracted[conc_key].clip(lower=0)
            df_extracted[conv_key] = df_extracted[conc_key].apply(
                lambda x: (1 - (x / init_conc)) * 100 if init_conc != 0 else 0
            )
        else:
            # Normalize concentration based on the maximum absorbance at the first time point
            max_abs = df_extracted[f"UV-Vis [{w} nm]"].iloc[1]
            df_extracted[conc_key] = df_extracted[f"UV-Vis [{w} nm]"].apply(
                lambda x: (x / max_abs) * init_conc if max_abs != 0 else 0
            )
            df_extracted[conc_key] = df_extracted[conc_key].clip(
                lower=0, upper=init_conc
            )

            # Calculate conversion based on the initial concentration
            df_extracted[conv_key] = df_extracted[conc_key].apply(
                lambda x: (1 - (x / init_conc)) * 100 if init_conc != 0 else 0
            )

    # Adding the highest wavelength as the concentration and conversion keys
    df_extracted[CONC_KEY] = df_extracted[conc_key]
    df_extracted[CONV_KEY] = df_extracted[conv_key]

    df_extracted = apply_time_shift(df_extracted, shift_min=7)

    return df_extracted


def get_solvent_IR_data(solvent_data_dir: str) -> pd.DataFrame:

    solvent_files = [
        os.path.join(solvent_data_dir, f)
        for f in os.listdir(solvent_data_dir)
        if f.endswith(".csv")
    ]

    if not solvent_files:
        raise FileNotFoundError(
            f"No solvent IR data files found in: {solvent_data_dir}"
        )

    solvent_files = sorted(solvent_files)
    ref_solvent_file = solvent_files[-2]

    return pd.read_csv(ref_solvent_file)


def read_IR_data(
    data_dir: str,
    sample_name: str,
    cutoff_time_min: Optional[int] = None,
    wavenumber: int = 1620,
    abs_coeff: float = 1.0,
) -> Optional[pd.DataFrame]:

    sample_data_dir = f"{data_dir}/IR/{sample_name}"
    solvent_data_dir = f"{data_dir}/IR/THF"

    # Check if the directories/files exist

    try:
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        elif not os.path.exists(sample_data_dir):
            raise FileNotFoundError(f"Sample IR data file not found: {sample_data_dir}")
        elif not os.path.exists(solvent_data_dir):
            raise FileNotFoundError(
                f"Solvent IR data file not found: {solvent_data_dir}"
            )

        solvent_data = get_solvent_IR_data(solvent_data_dir)

        sample_data_files = os.listdir(sample_data_dir)
        if not sample_data_files:
            raise FileNotFoundError(
                f"No sample IR data files found in: {sample_data_dir}"
            )
    except FileNotFoundError as e:
        print(e)
        return None

    # Loop through sample data files at each time
    data_list = []
    for data_file in sample_data_files:

        if not data_file.endswith(".csv"):
            continue

        # Load the sample data for a specified time
        sample_data_path = os.path.join(sample_data_dir, data_file)
        sample_data = pd.read_csv(sample_data_path)

        # Extract the time from the data
        time_str = sample_data.columns[1]  # Second column label is time
        time_min = convert_time_str_to_min(time_str)

        if cutoff_time_min is not None and time_min > cutoff_time_min:
            continue

        # Subtract the solvent data from the sample data
        sample_data.iloc[:, 1] = sample_data.iloc[:, 1] - solvent_data.iloc[:, 1]
        sample_data.iloc[:, 1] = sample_data.iloc[:, 1].clip(
            lower=0
        )  # Ensure no negative values

        # Get the absorbance value at the specified wavenumber
        if wavenumber not in sample_data["Wavenumbercm-1"].values:
            raise ValueError(
                f"Wavenumber {wavenumber} cm^-1 not found in the sample data."
            )
        abs_val = sample_data[sample_data["Wavenumbercm-1"] == wavenumber].iloc[0, 1]
        conc_val = abs_val / abs_coeff

        # Add time, absorbance, and concentration to the data list
        data_list.append([time_min, abs_val, conc_val])

    # Create a DataFrame from the collected data
    output_data = pd.DataFrame(
        data_list, columns=[TIME_KEY, f"Absorbance [{wavenumber} cm^-1]", CONC_KEY]
    ).sort_values(by=TIME_KEY)

    # Calculate conversion from
    init_conc = output_data.iloc[0][CONC_KEY]
    output_data[CONV_KEY] = output_data[CONC_KEY].apply(
        lambda x: (1 - (x / init_conc)) * 100 if x != 0 else 0
    )

    output_data = apply_time_shift(output_data, shift_min=7)

    return output_data


def read_NMR_data(data_dir: str, sample_name: str, **kwargs) -> Optional[pd.DataFrame]:
    return None


#################################
### Data Processing Functions ###
#################################


def apply_time_shift(data: pd.DataFrame, shift_min: float) -> pd.DataFrame:

    shifted_data = data.copy()
    shifted_data[TIME_KEY] = shifted_data[TIME_KEY] - shift_min
    shifted_data = shifted_data[shifted_data[TIME_KEY] >= 0].reset_index(drop=True)

    return shifted_data


def convert_time_str_to_min(time_str: str) -> float:
    h, m, s = map(int, time_str.split(":"))
    return h * 60 + m + s / 60


def create_output_dir(data_dir: str, sample_name: str) -> Tuple[str, str]:
    process_dir = os.path.join(data_dir, "Processed")
    figures_dir = os.path.join(process_dir, "Figures", sample_name)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    if not os.path.exists(process_dir):
        os.makedirs(process_dir)
    if not os.path.exists(figures_dir):
        os.makedirs(figures_dir)
    return process_dir, figures_dir


def process_all_data(
    data_dir: str,
    sample_name: str,
    uv_kwargs: Optional[dict] = None,
    ir_kwargs: Optional[dict] = None,
    nmr_kwargs: Optional[dict] = None,
) -> Dict[str, pd.DataFrame]:

    # Read data from the specified directories
    uv_data = read_UV_Vis_data(data_dir, sample_name, **(uv_kwargs or {}))
    ir_data = read_IR_data(data_dir, sample_name, **(ir_kwargs or {}))
    nmr_data = read_NMR_data(data_dir, sample_name, **(nmr_kwargs or {}))

    # Create directories for processed data and figures
    process_dir, figures_dir = create_output_dir(data_dir, sample_name)

    # Save processed data to CSV files
    if uv_data is not None:
        uv_path = os.path.join(process_dir, f"{sample_name}_{UV_VIS_KEY}.csv")
        uv_data.to_csv(uv_path, index=False)
    if ir_data is not None:
        ir_path = os.path.join(process_dir, f"{sample_name}_{IR_KEY}.csv")
        ir_data.to_csv(ir_path, index=False)
    if nmr_data is not None:
        nmr_path = os.path.join(process_dir, f"{sample_name}_{NMR_KEY}.csv")
        nmr_data.to_csv(nmr_path, index=False)

    data_dict = {
        UV_VIS_KEY: uv_data,
        IR_KEY: ir_data,
        NMR_KEY: nmr_data,
    }

    return data_dict


##################################
### Plotting Utility Functions ###
##################################
import matplotlib.pyplot as plt
from matplotlib.axes import Axes


def get_base_plot(**kwargs) -> tuple[plt.Figure, Axes]:
    return plt.subplots(figsize=(6, 4.5), dpi=300, **kwargs)


def plot_data(
    data_dict: Dict[str, pd.DataFrame],
    metric: str = CONC_KEY,
    cutoff_time_min: Optional[int] = None,
    output_filepath: Optional[str] = None,
    show: bool = False,
    **kwargs,
) -> Tuple[plt.Figure, Axes]:

    assert metric in [
        CONC_KEY,
        CONV_KEY,
    ], f'Invalid metric: {metric}. Must be one of "{CONC_KEY}", "{CONV_KEY}".'

    fig, ax = get_base_plot()

    for key, data in data_dict.items():

        assert (
            key in INSTRUMENT_KEYS
        ), f"Invalid key: {key}. Must be one of {INSTRUMENT_KEYS}."

        if data is None or data.empty:
            # print(f"No data available for {key}. Skipping.")
            continue

        color = COLORS[key]
        ax.plot(data[TIME_KEY], data[metric], label=key, color=color, **kwargs)

    if not ax.has_data():
        # print(f"No data to plot for metric: {metric}.")
        plt.close(fig)
        return fig, ax

    ax.set_xlabel(TIME_KEY)
    ax.set_ylabel(metric)
    ax.legend()

    # Adjust axes limits
    if metric == CONC_KEY:
        ax.set_ylim(0, None)
    elif metric == CONV_KEY:
        ax.set_ylim(0, 100)
    if cutoff_time_min is not None:
        ax.set_xlim(0, cutoff_time_min)

    # Save the figure if an output filepath is provided
    if output_filepath:
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        fig.savefig(output_filepath, bbox_inches="tight")
        # print(f"Figure saved to {output_filepath}")

    plt.tight_layout()
    if show:
        plt.show()
    elif output_filepath:
        plt.close(fig)

    return fig, ax


def plot_all_data(
    data_dict: Dict[str, pd.DataFrame],
    data_dir: Optional[str] = None,
    sample_name: str = "",
    show: bool = False,
    **kwargs,
):

    if data_dir is not None:
        _, figures_dir = create_output_dir(data_dir, sample_name)

    for key, data in data_dict.items():

        conv_path = (
            os.path.join(figures_dir, f"{sample_name}_{key}_conv.png")
            if figures_dir
            else None
        )
        conc_path = (
            os.path.join(figures_dir, f"{sample_name}_{key}_conc.png")
            if figures_dir
            else None
        )

        plot_data(
            {key: data},
            metric=CONC_KEY,
            output_filepath=conc_path,
            show=show,
            **kwargs,
        )
        plot_data(
            {key: data},
            metric=CONV_KEY,
            output_filepath=conv_path,
            show=show,
            **kwargs,
        )

    # Plot all data together
    conv_path = (
        os.path.join(figures_dir, f"{sample_name}_all_conv.png")
        if figures_dir
        else None
    )
    conc_path = (
        os.path.join(figures_dir, f"{sample_name}_all_conc.png")
        if figures_dir
        else None
    )

    plot_data(
        data_dict,
        metric=CONC_KEY,
        output_filepath=conc_path,
        show=show,
        **kwargs,
    )
    plot_data(
        data_dict,
        metric=CONV_KEY,
        output_filepath=conv_path,
        show=show,
        **kwargs,
    )
