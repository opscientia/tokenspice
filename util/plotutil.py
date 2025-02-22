import copy
import csv
from enforce_typing import enforce_types
import logging
import matplotlib
from matplotlib import pyplot
import numpy
from pylab import figure, axes, pie, title, show
from typing import Any, List, Union

from util.constants import * #S_PER_YEAR etc

LINEAR, LOG, BOTH = 0, 1, 2 #pyplot.yscale interprets 1st 2
MULT1, MULT100, DIV1M, DIV1B = 0, 1, 2, 3 #multiply or divide the value?
COUNT, DOLLAR, PERCENT = 0, 1, 2

@enforce_types
class YParam:
    """Defines what to plot for y-values. 
    See example usage in netlist_headerValuesToXY.
    """
    def __init__(
            self,
            y_header_names: List[str],
            labels: List[str],
            y_pretty_name: str,
            y_scale: int, #one of LINEAR, LOG, BOTH
            mult: int,    #one of MULT1, MULT100, DIV1M, DIV1B
            unit: int     #one of COUNT, DOLLAR, PERCENT
    ):
        
        self.y_header_names = y_header_names
        self.labels = labels
        self.y_pretty_name = y_pretty_name
        self.y_scale = y_scale 
        self.mult = mult 
        self.unit = unit 

    @property
    def y_scale_str(self):
        if   self.y_scale == LINEAR:  return "LINEAR"
        elif self.y_scale == LOG:     return "LOG"
        elif self.y_scale == BOTH:    return "BOTH"
        else: raise ValueError(self.y_scale)

@enforce_types
def arrayToFloatList(x_array) -> List[float]:
    """
    :param: x_array: array[Any]
    :return: List[float]
    """
    return [float(x_item) for x_item in x_array]

@enforce_types
def _applyMult(y: List[float], mult:int) -> List[float]:
    """
    Apply multiplier according to enum specified by 'mult'

    :param: y: values
    :param: mult: e.g. MULT1, DIV1B, ..
    :return: y multiplied
    """
    if mult == MULT1:
        return list(numpy.array(y) * 1.0)
    elif mult == MULT100:
        return list(numpy.array(y) * 100.0)
    elif mult == DIV1M:
        return list(numpy.array(y) / 1e6)
    elif mult == DIV1B:
        return list(numpy.array(y) / 1e9)
    else:
        raise ValueError(mult)

@enforce_types
def _multUnitStr(mult:int, unit:int) -> str:
    """
    String describing units of a given enum multiplier

    :param: mult: e.g. MULT1, DIV1B, ..
    :param: unit: e.g. DOLLAR, COUNT
    :return: "$", "count, in billions"
    """
    if mult == MULT1 and unit == DOLLAR:
        return "$"
    elif mult == DIV1M and unit == DOLLAR:
        return "$M"
    elif mult == DIV1B and unit == DOLLAR:
        return "$B"
    elif mult == MULT1 and unit == COUNT:
        return "count"
    elif mult == DIV1M and unit == COUNT:
        return "count, in millions"
    elif mult == DIV1B and unit == COUNT:
        return "count, in billions"
    elif mult == MULT100 and unit == PERCENT:
        return "%"
    else:
        raise ValueError(f"can't handle mult={mult} with unit={unit}")
    return

@enforce_types
def _expandBOTHinY(y_params: List[YParam]) -> List[YParam]:
    """
    Any y_param that has a BOTH gets expanded to a LOG & a LINEAR entry

    :param: y_params -- incoming list of what to plot
    :return: y_params2 -- revised list
    """
    #replace BOTH with 2 entries
    y_params2 = []
    for p in y_params:
        if p.y_scale in [LINEAR, BOTH]:
            p2 = copy.copy(p)
            p2.y_scale = LINEAR
            y_params2.append(p2)
        if p.y_scale in [LOG, BOTH]:
            p2 = copy.copy(p)
            p2.y_scale = LOG
            y_params2.append(p2)
    return y_params2

@enforce_types
def _xyToPngs(header: List[str], values,
              x: List[float], y_params: List[YParam],
              output_png_dir: str):
    """
    Given actual data (header, values) and what to plot (x, y_params),
    create plots and store as .png files in output_png_dir

    :param: header: List[str] holding 'Tick', 'Second', ...
    :param: values: 2d array of float [tick_i, valuetype_i]
    :param: x: x-axis info on how to plot
    :param: y_params: y-axis info on how to plot
    :param: output_png_dir: path of output png to be created and filled
    :return: <None> but creates png directory
    """
    
    assert not os.path.exists(output_png_dir)
    os.mkdir(output_png_dir)

    for p in y_params:
        ys = [arrayToFloatList(values[:,header.index(name)])
              for name in p.y_header_names]

        ys = [_applyMult(y, p.mult) for y in ys]

        fig, ax = pyplot.subplots()
        
        ax.set_xlabel("Month")
        
        for y, label in zip(ys, p.labels):
            if label == "":
                ax.plot(x, y)
            else:
                ax.plot(x, y, label=label)
        if len(p.labels) > 1 and len(p.labels) <= 5:
            ax.legend()

        mult_unit_s = _multUnitStr(p.mult, p.unit)
        ax.set_ylabel(f"{p.y_pretty_name} ({mult_unit_s})")
        
        ax.set_title(f"{p.y_pretty_name}" + f" ({p.y_scale_str})")
        
        pyplot.yscale(p.y_scale_str)
        
        if p.y_scale == LOG: #turn off exponential notation 
            ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())

        ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2g'))
        max_y = max([max(y) for y in ys])
        if max_y < 1000.0:
            ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2f'))
        
        max_x = max(10, math.ceil(max(x)))
        if max_x < 12:
            xticks = list(range(max_x+1))
        elif max_x < 22:
            xticks = [i for i in range(max_x+1) if (i%2)==0]
        elif max_x < 52:
            xticks = [i for i in range(max_x+1) if (i%5)==0]
        elif max_x < 152:
            xticks = [i for i in range(max_x+1) if (i%10)==0]
        elif max_x < 202:
            xticks = [i for i in range(max_x+1) if (i%20)==0]
        elif max_x > 202:
            xticks = [i for i in range(max_x+1) if (i%20)==0]
        pyplot.xticks(xticks)

        #pyplot.show() #popup

        base_output_filename = f"{p.y_pretty_name}_{p.y_scale_str}.png".replace('/',"_per_").replace(" ","_").replace(",","_").replace("'","").replace("__","_")
        full_output_filename = os.path.join(output_png_dir, base_output_filename)
        pyplot.savefig(full_output_filename,bbox_inches='tight') 
        print(f"Created '{full_output_filename}'")

    return

@enforce_types
def _csvToHeaderValues(input_csv_filename: str):
    """
    Given csv file from a TokenSPICE run, creates (header, values).

    :param: input_csv_filename absolute path of input csv file
    :param: output_png_dir: path of output png to be created and filled
    :param: netlist_headerValuesToXY: function defined by netlist that
      converts (header, values) to (x, y_params)
     
    :return: header -- List[str] holding 'Tick', 'Second', ...
    :return: values -- 2d array of float [tick_i, valuetype_i]
    """    
    assert os.path.exists(input_csv_filename)
    header: Any = None
    values: Any = []
    with open(input_csv_filename, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        for row in csvreader: #row = ['Tick', 'Second', ..] or [1.0, 100.0, ..]
            if header is None:
                header = row
                header = [param.strip() for param in header]
            else:
                values.append(row)
    values = numpy.array(values) #[tick_i, valuetype_i]
    return (header, values)
        
@enforce_types
def csvToPngs(input_csv_filename: str, output_png_dir: str,
              netlist_plot_instrs_func):
    """
    Main plotting routine, delegates subtasks to worker routines.

    :param: input_csv_filename absolute path of input csv file
    :param: output_png_dir: path of output png to be created and filled
    :param: netlist_headerValuesToXY: function defined by netlist that
      converts (header, values) to (x, y_params)
     
    :return: <None> but creates png directory
    """
    (header, values) = _csvToHeaderValues(input_csv_filename)

    (x, y_params) = netlist_plot_instrs_func(header, values)
    y_params = _expandBOTHinY(y_params)

    _xyToPngs(header, values, x, y_params, output_png_dir)

