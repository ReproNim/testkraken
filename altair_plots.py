import altair as alt
import bs4
import os
import pandas as pd


class AltairPlots(object):
    def __init__(self, wf_dir, results_df, plot_spec):
        self.wf_dir = wf_dir
        self.index = os.path.join(self.wf_dir, "index.html")
        self.plot_spec = plot_spec
        self._soup = self._index_read()
        self.results = results_df


    def create_plots(self):
        for ii, spec in enumerate(self.plot_spec):
            self._index_edit(title=spec["function"], id=ii)
            plot_dict = getattr(self, spec["function"])(spec["var_list"])
            self._js_create(plot_dict, ii)
        self._index_write()

    def scatter_all(self, var_l):
        res_plot = self.results[eval(var_l)+["env"]]
        res_transf = res_plot.reset_index().melt(['env', 'index'])
        plot_dict = alt.Chart(res_transf).mark_circle(
                size=50, opacity=0.5).encode(
                x='variable:N',
                y='value:Q',
                color='env:N').properties(
                width=400).interactive().to_dict()
        return plot_dict


    def _js_create(self, plot_dict, id):
        js_str = 'var var{} = {}\n vegaEmbed("#alt_{}", var{});'.format(
            id, plot_dict, id, id)
        with open(os.path.join(self.wf_dir, "alt_{}.js".format(id)), "w") as outf:
            outf.write(js_str)


    def _index_read(self):
        with open(self.index) as inf:
            txt = inf.read()
            soup = bs4.BeautifulSoup(txt, 'html.parser')
        return soup

    def _index_write(self):
        with open(self.index, "w") as outf:
            outf.write(str(self._soup))

    def _index_edit(self, title, id):
        new_tag = self._soup.new_tag("h3")
        new_tag.append(title)
        self._soup.body.append(new_tag)

        new_div = self._soup.new_tag("div", id="alt_{}".format(id))
        self._soup.body.append(new_div)

        new_script = self._soup.new_tag("script", src="alt_{}.js".format(id))
        self._soup.body.append(new_script)
