import altair as alt
import bs4
import os, pdb


class AltairPlots(object):
    def __init__(self, wf_dir, results_df, results_df_flat, plot_spec):
        self.wf_dir = wf_dir
        self.index = os.path.join(self.wf_dir, "index.html")
        self.plot_spec = plot_spec
        self._soup = self._index_read()
        self.results = results_df
        self.results_flat = results_df_flat
        self.plot_description = {
            "scatter_all": "scatter plot for all environments",
            "scatter_2var": "scatter two tests results for all environments",
            "barplot_all": "barplot for all environments",
            "barplot_all_rel_error": "barplot of the relative errors for all environments",
        }
        self.drop_key_list_default = [
            "python",
            "base",
            "fsl",
            "conda_install",
            "pip_install",
        ]

    def create_plots(self):
        for ii, spec in enumerate(self.plot_spec):
            if spec["function"] not in self.plot_description.keys():
                raise Exception(
                    "{} is not available, available plotting functions: {}".format(
                        spec["function"], list(self.plot_description.keys())
                    )
                )
            self._index_edit(title=self.plot_description[spec["function"]], id=ii)
            plot_dict = getattr(self, spec["function"])(spec["var_list"])
            self._js_create(plot_dict, ii)
        self._index_write()

    def scatter_all(self, var_l):
        if not var_l:
            # if var_l is not provided, I will plot all
            var_l = [
                col
                for col in self.results_flat.columns
                if col not in self.drop_key_list_default
            ]
        res_plot = self.results_flat[var_l].fillna("NaN")
        res_transf = res_plot.reset_index().melt(["env", "index"])
        plot_dict = (
            alt.Chart(res_transf)
            .mark_circle(size=50, opacity=0.5)
            .encode(x="variable:N", y="value:Q", color="env:N")
            .properties(width=400, background="white")
            .interactive()
            .to_dict()
        )
        return plot_dict

    def scatter_2var(self, var_scat):
        plot = []
        for var in var_scat:
            res_plot = self.results[var + ["env"]].fillna("NaN")
            plot_el = (
                alt.Chart(res_plot)
                .mark_circle(size=50, opacity=0.5)
                .encode(x="{}:Q".format(var[0]), y="{}:Q".format(var[1]), color="env:N")
                .properties(width=400)
                .interactive()
            )
            plot.append(plot_el)
        plot_dict = alt.hconcat(*plot).properties(background="white").to_dict()
        return plot_dict

    def barplot_all(self, var_l, y_scale=None, y_max_check=False, default_col="test"):
        if not var_l:
            # if var_l is not provided, I will plot all
            var_l = [col for col in self.results_flat.columns if default_col in col]
        res_plot = self.results_flat[var_l + ["env"]].fillna("NaN")
        res_transf = res_plot.reset_index().melt(["env", "index"])
        if y_scale:  # should be a tuple, TODO
            if y_max_check:
                y_max = round(self.results_flat[var_l].max().max() + 0.1, 2)
                y_scale_update = (y_scale[0], y_max)
                y_bar = alt.Y("value:Q", scale=alt.Scale(domain=y_scale_update))
            else:
                y_bar = alt.Y("value:Q", scale=alt.Scale(domain=y_scale))
        else:
            y_bar = "value:Q"
        base = (
            alt.Chart(res_transf)
            .mark_bar()
            .encode(y=y_bar, x="variable:N", color="env:N")
            .properties(width=400)
        )
        chart = alt.hconcat().properties(background="white")
        for env in [ee for ee in self.results_flat.env if ee != "N/A"]:
            chart |= base.transform_filter(alt.expr.datum.env == env)
        plot_dict = chart.to_dict()
        return plot_dict

    def barplot_all_rel_error(self, var_l):
        return self.barplot_all(
            var_l, y_scale=(0, 1), y_max_check=True, default_col="rel_error"
        )

    def _js_create(self, plot_dict, id):
        js_str = 'var var{} = {}\n vegaEmbed("#alt_{}", var{});'.format(
            id, plot_dict, id, id
        )
        with open(os.path.join(self.wf_dir, "alt_{}.js".format(id)), "w") as outf:
            outf.write(js_str)

    def _index_read(self):
        with open(self.index) as inf:
            txt = inf.read()
            soup = bs4.BeautifulSoup(txt, "html.parser")
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
