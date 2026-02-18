import datetime
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator
from matplotlib.ticker import AutoMinorLocator
from matplotlib.patches import Patch
from argparse import ArgumentParser
import pandas as pd
from .base import BasePlot

class GanttChart(BasePlot):
    '''A class for plotting a Gantt chart given a csv file of tasks.'''

    def __init__(self, task_csv = 'rrndbd/data/mitacs_18_weeks.csv', **kwargs):
        '''Instantiates a Gantt chart'''

        super().__init__(figsize = (8,4), **kwargs)
        
        tasks = self.load_tasks_from_csv(task_csv)
        self.set_dates(2026, 4, 27)
        self.set_phase_colours()

        ax = self.ax

        ax.barh(y = tasks['task'], width = tasks['duration'], left = tasks['start_date'], color = tasks['colour'])
        ax.invert_yaxis()
        date_form = DateFormatter('%B %d')
        ax.xaxis.set_major_formatter(date_form)
        ax.xaxis.set_minor_locator(WeekdayLocator(byweekday=0))
        # ax.get_yaxis().set_visible(False)
        ax.grid(
            True,
            which="major",
            axis="x",
            linewidth=0.5,
            linestyle="-",
            alpha=0.8,
        )

        # Minor gridlines: weeks
        ax.grid(
            True,
            which="minor",
            axis="x",
            linewidth=0.4,
            linestyle="--",
            alpha=0.8,
        )

        # for i, task in tasks.iterrows():
        #     ax.text(task['start_date'], i, f'  {task['task']}', ha='right', va='center', color='black', fontweight='bold')

        # ax.get_yaxis().set_visible(False)
        self.add_legend()

    def load_tasks_from_csv(self, task_csv):
        '''Loads in the file of csv-listed tasks as long as it isn't empty.'''

        tasks = pd.read_csv(task_csv)

        if not tasks.empty:
            self.tasks = tasks
    
        return tasks
    
    def set_dates(self, yr, mnth, d):
        '''The csv file has week numbers instead of dates. This function allows dates to be set instead of week numbers. We just need a start date.'''

        t0 = datetime.datetime(yr, mnth, d)
        self.start_date = t0

        # Make a more convenient pointer
        tasks = self.tasks

        # check to make sure there are week numbers
        if 'start_week' in tasks.keys() and not tasks['start_week'].isnull().all():
                
            tasks['start_date'] = t0 + pd.to_timedelta(tasks['start_week'], unit='W')
            tasks['end_date']   = t0 + pd.to_timedelta(tasks['end_week'],   unit='W')
            tasks['duration'] = tasks['end_date'] - tasks['start_date']

    def set_phase_colours(self):
        '''Numbers the phases... Needs to be more generalized, but we'll get there '''
        tasks = self.tasks
        phase_map = {
            "Pilot": 1,
            "Development": 2,
            "Execution": 3,
            "Publication": 4,
        }
        tasks["phase_num"] = tasks["phase"].map(phase_map)
        tasks["colour"] = tasks["phase_num"].apply(lambda n: self.colours[n - 1])


    def add_legend(self):
        '''Adds the right colours and labels for the tasks and phases'''

        # Create a list of custom patches for the legend
        colours = self.colours
        ax = self.ax
        tasks = self.tasks
        phases = tasks.drop_duplicates(subset = 'phase').sort_index()


        legend_elements = [Patch(facecolor=colours[task['phase_num'] - 1], label = task['phase']) for _, task in phases.iterrows()]


        # Add the legend in the top right corner of the plot
        ax.legend(handles=legend_elements, loc='upper right', title='Phases',
                facecolor='white', 
                edgecolor='white', 
                # fontsize=10, 
                # title_fontsize=12, 
                frameon=True
                )
        


def main():
    this_gantt = GanttChart()
    this_gantt.show()


if __name__ == "__main__":
    main()