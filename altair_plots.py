import altair as alt
import bs4
import os, pdb
import pandas as pd


class AltairPlots(object):
    def __init__(self, wf_dir, results_df, plot_spec):
        self.wf_dir = wf_dir
        self.index = os.path.join(self.wf_dir, "index.html")
        self.plot_spec = plot_spec
        self._soup = self._index_read()
        self.results = results_df
        self.plot_description = {"scatter_all": "scatter plot for all environments",
                                 "barplot_all": "barplot for all environments",
                                 "barplot_all_rel_error": "barplot of the relative errors for all environments"}

    def create_plots(self):
        for ii, spec in enumerate(self.plot_spec):
            self._index_edit(title=self.plot_description[spec["function"]], id=ii)
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
                width=400, background="#a9a3b7").interactive().to_dict()
        return plot_dict


    def barplot_all(self, var_l, y_scale=None):
        res_plot = self.results[eval(var_l)+["env"]]
        res_transf = res_plot.reset_index().melt(['env', 'index'])
        if y_scale: #should be a tuple, TODO
            y_bar = alt.Y('value:Q', scale=alt.Scale(domain=y_scale))
        else:
            y_bar = 'value:Q'
        base = alt.Chart(res_transf).mark_bar(
                ).encode(
                y=y_bar,
                x='variable:N',
                color='env:N').properties(
                width=400)
        chart = alt.hconcat().properties(background="#a9a3b7")
        for env in [ee for ee in self.results.env if ee != "N/A"]:
            chart |= base.transform_filter(alt.expr.datum.env == env)

        plot_dict = chart.to_dict()
        return plot_dict


    def barplot_all_rel_error(self, var_l):
        return self.barplot_all(var_l, y_scale=(0,1))


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
        new_break = self._soup.new_tag("p")
        self._soup.body.find_all("h2")[-1].append(new_break)

        new_tag = self._soup.new_tag("h3")
        new_tag.append(title)
        self._soup.body.find_all("h2")[-1].append(new_tag)

        new_div = self._soup.new_tag("div", id="alt_{}".format(id))
        self._soup.body.find_all("h2")[-1].append(new_div)

        new_script = self._soup.new_tag("script", src="alt_{}.js".format(id))
        self._soup.body.find_all("h2")[-1].append(new_script)
