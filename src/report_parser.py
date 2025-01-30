from vivado_report_parser import parse_vivado_report
from pathlib import Path
import toml


def get_dict_from_vivado_report(report_filepath: Path) -> dict:
    report_text = ""
    with open(report_filepath, "r") as f:
        for line in f:
            report_text += line
    report_dict = parse_vivado_report(report_text)
    return report_dict


def get_toml_string(d: dict) -> str:
    return toml.dumps(d)


def create_toml_from_vivado_report(report_filepath: Path, toml_destination_filepath: Path) -> dict:
    report_dict = get_dict_from_vivado_report(report_filepath)
    toml_string = get_toml_string(report_dict)
    with open(toml_destination_filepath, "w") as f:
        f.write(toml_string)
    return report_dict


def main():
    report_filepath = Path("../tmp/client/dominik/41/result/reports/env5_top_reconfig_power_routed.rpt")
    report_dict = get_dict_from_vivado_report(report_filepath)
    print(get_toml_string(report_dict))


if __name__ == "__main__":
    main()
