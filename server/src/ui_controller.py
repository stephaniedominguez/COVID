from flask import Flask, render_template


def map():
    return render_template("map_plot.html", template_folder='template')
