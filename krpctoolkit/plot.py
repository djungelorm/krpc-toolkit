from collections import deque
import matplotlib.pyplot as plot

class LivePlot(object):
    def __init__(self, series, defaultopt, window):

        data = {}
        for name,opt in series:
            data[name] = deque([None] * window)

        self.fig = plot.figure(1)
        axes = {}
        for i,(name,opt) in enumerate(series):

            mergedopt = defaultopt.copy()
            mergedopt.update(opt)
            opt = mergedopt

            ylim = opt.get('ylim', (-1,1))
            ylabel = opt.get('ylabel', name)
            yticks = opt.get('yticks', [ylim[0], (ylim[1]-ylim[0])/2 + ylim[0], ylim[1]])
            grid = opt.get('grid', 'lightgrey')

            axis = self.fig.add_subplot(len(series),1,i+1)
            axis.axis([0,window,ylim[0],ylim[1]])
            axis.set_xlabel('')
            axis.set_xticks([])
            axis.set_ylabel(ylabel)
            axis.set_yticks(yticks)
            axis.set_ylim(ylim)
            if grid:
                for tick in yticks:
                    axis.axhline(y=tick, ls='-', color=grid)
            axes[name] = axis

        lines = {}
        for i,(name,opt) in enumerate(series):

            mergedopt = defaultopt.copy()
            mergedopt.update(opt)
            opt = mergedopt

            color = opt.get('color', 'black')
            line = axes[name].plot(list(range(window)), data[name], '-', color=color)
            lines[name] = line

        plot.ion()
        self.fig.show()

        self.series = series
        self.data = data
        self.lines = lines

    def add(self, values):
        for i,(name,opt) in enumerate(self.series):
            self.data[name].append(values[i])
            self.data[name].popleft()
            self.lines[name][0].set_ydata(self.data[name])

    def draw(self):
        plot.draw()
