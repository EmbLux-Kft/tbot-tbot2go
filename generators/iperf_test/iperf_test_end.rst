
Our current test has iperf_result.

What does tbot in this testcase?

tbot parses the output of :redtext:`iperf` and compares the values in
column :redtext:`Bandwidth` with the minimum value of iperf_minval iperf_unit
we passed to the tbot testcase. For later usage tbot also writes the
values into a textfile, which for example gnuplot can parse.

Extracted values
----------------

.. include:: ../iperf/iperf.dat
   :literal:

.. raw:: pdf

   PageBreak

Created Image
-------------

based on the extracted values, gnuplot can generate the following diagram:

.. image:: ../iperf/iperf.jpg
