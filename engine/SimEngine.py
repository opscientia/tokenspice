import logging
log = logging.getLogger('master')

from enforce_typing import enforce_types
import os

from util import valuation
from util.constants import S_PER_MIN, S_PER_HOUR, S_PER_DAY, S_PER_MONTH, S_PER_YEAR

@enforce_types
class SimEngine(object):
    """
    @description
      Runs a simulation.
      
    @attributes
      state - child of SimState
      output_dir -- directory of where results are stored
    """

    def __init__(self, state, output_dir: str, netlist_log_func=None):
        self.state = state
        self.output_dir = output_dir
        self.output_csv = "data.csv" #magic number
        self.netlist_log_func = netlist_log_func
        
    def run(self):
        """
        @description
          Runs the simulation!  This is the main work routine.
        
        @return
           <<none>> but it continually generates an output csv output_dir
        """
        log.info("Begin.")
        log.info(str(self.state.ss) + "\n")

        while True:
            self.takeStep()
            if self.doStop():
                break
            self.state.tick += 1 #could be e.g. 10 or 100 or ..
        log.info("Done")

    def takeStep(self) -> None:
        """Run one tick, updates self.state"""
        log.debug("=============================================")
        log.debug("Tick=%d: begin" % (self.state.tick))
        
        if (self.elapsedSeconds() % S_PER_DAY) == 0:
            s, dataheader, datarow  = self.createLogData()            
            log.info("".join(s))
            self.logToCsv(dataheader, datarow)
                
        #main work
        self.state.takeStep()
        
        log.debug("=============================================")
        log.debug("Tick=%d: done" % self.state.tick)

    def createLogData(self):
        """Compute this iter's status, and output in forms ready
        for console logging and csv logging."""
        state = self.state
        ss = state.ss
        kpis = state.kpis

        s = [] #for console logging
        dataheader = [] # for csv logging: list of string
        datarow = [] #for csv logging: list of float

        #columns always logged: Tick, Second, Min, Hour, Day, Month, Year
        s += ["Tick=%d" % (state.tick)]
        dataheader += ["Tick"]
        datarow += [state.tick]

        es = float(self.elapsedSeconds())
        emi, eh, ed, emo, ey = es/S_PER_MIN, es/S_PER_HOUR, es/S_PER_DAY, \
                               es/S_PER_MONTH,es/S_PER_YEAR
        s += [" (%.1f h, %.1f d, %.1f mo, %.1f y)" % \
              (eh, ed, emo, ey)] 
        dataheader += ["Second", "Min", "Hour", "Day", "Month", "Year"]
        datarow += [es, emi, eh, ed, emo, ey]

        #other columns to log
        if self.netlist_log_func is not None:
            s2, dataheader2, datarow2 = self.netlist_log_func(state)
            s += s2
            dataheader += dataheader2
            datarow += datarow2

        return s, dataheader, datarow

    def logToCsv(self, dataheader, datarow) -> None:
        if self.output_dir is None:
            return
                
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
            
        full_filename = os.path.join(self.output_dir, self.output_csv)
        
        #if needed, create file and add header
        if not os.path.exists(full_filename):
            with open(full_filename,'w+') as f:
                f.write(", ".join(dataheader) + "\n")
            
        #add in row
        datarow_s = ['%g' % dataval for dataval in datarow]
        with open(full_filename,'a+') as f:
            f.write(", ".join(datarow_s) + "\n")

    def elapsedSeconds(self) -> int:
        return self.state.tick * self.state.ss.time_step

    def doStop(self) -> bool:
        if self.state.tick >= self.state.ss.max_ticks:
            log.info("Stop: tick (%d) >= max" % self.state.tick)
            return True
        
        return False
            
