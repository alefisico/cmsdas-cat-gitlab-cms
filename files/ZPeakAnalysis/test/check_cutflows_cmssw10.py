#!/usr/bin/env python
import sys
import argparse

def parse_integral_file(filename):
    """Parses the text file and returns a dictionary of {variable: value}."""
    data = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                if ':' in line:
                    parts = line.split(':')
                    key = parts[0].replace('Integral of ', '').strip()
                    value = float(parts[1].strip())
                    data[key] = value
        return data
    except IOError:
        print "Error: File '{0}' not found.".format(filename)
        sys.exit(1)
    except Exception as e:
        print "Error parsing '{0}': {1}".format(filename, e)
        sys.exit(1)

def compare(file1, file2, tolerance=1e-6):
    data1 = parse_integral_file(file1)
    data2 = parse_integral_file(file2)

    all_keys = set(data1.keys()).union(set(data2.keys()))
    match = True

    print "{0:<20} | {1:<15} | {2:<15} | {3}".format('Variable', 'File 1', 'File 2', 'Status')
    print "-" * 70

    for key in sorted(all_keys):
        val1 = data1.get(key, None)
        val2 = data2.get(key, None)

        if val1 is None or val2 is None:
            status = "MISSING"
            match = False
        elif abs(val1 - val2) <= tolerance:
            status = "PASS"
        else:
            status = "FAIL"
            match = False

        print "{0:<20} | {1:<15} | {2:<15} | {3}".format(key, str(val1), str(val2), status)

    return match

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare CMSSW integral outputs.")
    parser.add_argument("file1", help="First txt file (reference)")
    parser.add_argument("file2", help="Second txt file (new run)")
    args = parser.parse_args()

    if compare(args.file1, args.file2):
        print "\nSUCCESS: The files match."
        sys.exit(0)
    else:
        print "\nFAILURE: Differences detected between the runs."
        sys.exit(1)
