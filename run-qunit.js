/**
 * PhantomJS: QUnit test runner from https://github.com/ariya/phantomjs/blob/1.2/examples/run-qunit.js
 *
 * Wait until the test condition is true or a timeout occurs. Useful for waiting
 * on a server response or for a ui change (fadeIn, etc.) to occur.
 *
 * @param testFx javascript condition that evaluates to a boolean,
 * it can be passed in as a string (e.g.: "1 == 1" or "$('#bar').is(':visible')" or
 * as a callback function.
 * @param onReady what to do when testFx condition is fulfilled,
 * it can be passed in as a string (e.g.: "1 == 1" or "$('#bar').is(':visible')" or
 * as a callback function.
 * @param timeOutMillis the max amount of time to wait. If not specified, 3 sec is used.
 */
function waitFor(testFx, onReady, onError, timeOutMillis) {
    var maxtimeOutMillis = timeOutMillis ? timeOutMillis : 3001, //< Default Max Timout is 3s
    start = new Date().getTime(),
    condition = false,
    interval = setInterval(function() {
        if ( (new Date().getTime() - start < maxtimeOutMillis) && !condition ) {
            // If not time-out yet and condition not yet fulfilled
            condition = (typeof(testFx) === "string" ? eval(testFx) : testFx()); //< defensive code
        } else {
            if(!condition) {
                // If condition still not fulfilled (timeout but condition is 'false')
                onError("'waitFor()' timeout");
                phantom.exit(1);
            } else {
                // Condition fulfilled (timeout and/or condition is 'true')
                typeof(onReady) === "string" ? eval(onReady) : onReady(); //< Do what it's supposed to do once the condition is fulfilled
                clearInterval(interval); //< Stop this interval
            }
        }
    }, 100); //< repeat check every 100ms
};

function ISODateString(d) {
    function pad(n){
        return n<10 ? '0'+n : n
    }
    return d.getUTCFullYear()+'-'
      + pad(d.getUTCMonth()+1)+'-'
      + pad(d.getUTCDate())+'T'
      + pad(d.getUTCHours())+':'
      + pad(d.getUTCMinutes())+':'
      + pad(d.getUTCSeconds())+'Z'
}

function unescapeHtml(str) {
    str = str.replace(/</g,"&lt;")
    str = str.replace(/>/g,"&gt;");
    str = str.replace(/&/g,"&amp;");
    str = str.replace(/"/g,"&quot;");
    return str;
}

function filterChildrenByType(node, typeName) {
    var nodes = new Array();

    for (var i=0; i < node.childNodes.length; i++) {
        var sub = node.childNodes[i];

        if (typeof(sub.tagName) == 'undefined') {
            continue;

        } else if (sub.tagName.toLowerCase() != typeName.toLowerCase()) {
            continue;
        }

        nodes.push(sub);

    }

    return nodes;
}

function getChildByClass(node, classname) {
    for (var i=0; i < node.childNodes.length; i++) {
        var sub = node.childNodes[i];

        if (typeof(sub.getAttribute('class')) == 'undefined') {
            continue;

        } else if (sub.getAttribute('class').indexOf(classname) > -1) {
            return sub;
        }
    }

    return null;
}

function formatTestresultTable(test) {
    var table = test.getElementsByTagName('table')[0];

    var trs = table.getElementsByTagName('tr');
    var tabletext = [];
    for (var r=0; r < trs.length; r++) {
        var tds = trs[r].childNodes;

        var rowtext = [];
        for (var d=0; d < tds.length; d++) {
            var td = tds[d];
            rowtext.push(unescapeHtml(td.innerText));
        }
        tabletext.push(rowtext.join(' '));
    }
    return tabletext;
}

function JUnitXMLReportWriter(suitename, result) {
    this.start_testsuite = function(failures, total, timestamp, duration) {
        console.log(
            '<testsuite name="' + suitename + '" ' +
              'failures="' + failures + '" ' +
              'tests="' + total + '" ' +
              'errors="0" ' +
              'timestamp="' + timestamp + '" ' +
              'time="' + duration + '">');
    };

    this.end_testsuite = function(failures, total, timestamp, duration) {
        console.log('</testsuite>');
    };

    this.start_testcase = function(modulename, testname, has_failures) {
        var classname = suitename + '.' + modulename;
        console.log(
            '  <testcase classname="' + classname + '" ' +
              'name="testname">');
    };

    this.testcase_failure = function(message, type, details) {
        message = unescapeHtml(message);
        type = unescapeHtml(type);
        console.log(
            '    <failure ' +
              'message="' + unescapeHtml(message) +'" ' +
              'type="' + type + '">');
        console.log(details.join('\n'));
        console.log('</failure>')
    };

    this.end_testcase = function(modulename, testname, has_failures) {
        console.log('  </testcase>');
    };

    return this;
}

function ConsoleReportWriter(suitename, result) {
    this.start_testsuite = function(failures, total, timestamp, duration) {
        console.log('Running '.concat(suitename));
        console.log('');
    };

    this.end_testsuite = function(failures, total, timestamp, duration) {
        console.log(
            'Total: '.concat(total).concat(', ').concat(
                failures).concat(' failures, in ').concat(
                    duration).concat(' seconds.'));
        console.log('');
    };

    this.start_testcase = function(modulename, testname, has_failures) {
        if (has_failures) {
            console.log('  ' + modulename + ': ' + testname);
        }
    };

    this.testcase_failure = function(message, type, details) {
        console.log('    ' + message);
        console.log('        ' + details.join('\n        '));
    };

    this.end_testcase = function(modulename, testname, has_failures) {
        if (has_failures) {
            console.log('');
        }
    };

    return this;
}



function generate_report(suitename, result, writertype) {
    var writer = writertype(suitename, result);

    var summaryArr = result.testresult.split("\n",3);
    var durationLine = summaryArr[0];
    var countLine = summaryArr[1];

    var duration = durationLine.match(
          /Tests completed in (\d+) milliseconds./)[1] / 1000;
    var countMatch = countLine.match(
          /(\d+) tests of (\d+) passed, (\d+) failed./);
    var testCount = countMatch[2];
    var failures = countMatch[3];
    var timestamp = ISODateString(new Date());

    writer.start_testsuite(failures, testCount, timestamp, duration);

    var testList = document.createElement("ol");
    testList.innerHTML = result.tests_html;
    var testcase_nodes = filterChildrenByType(testList, 'li');

    for (var i=0; i < testcase_nodes.length; i++) {
        var testcase = testcase_nodes[i];
        var modulename = filterChildrenByType(
            filterChildrenByType(testcase, 'strong')[0], 'span')[0].innerText;
        var testname = filterChildrenByType(
            filterChildrenByType(testcase, 'strong')[0], 'span')[1].innerText;

        var has_failures = testcase.getAttribute('class') == 'fail';

        writer.start_testcase(modulename, testname, has_failures);

        var tests = filterChildrenByType(
            filterChildrenByType(testcase, 'ol')[0], 'li');
        for (var j=0; j < tests.length; j++) {
            var test = tests[j];

            if (test.getAttribute('class') == 'pass') {
                continue;
            }

            var message = getChildByClass(test, 'test-message').innerText;
            var details = formatTestresultTable(test);
            writer.testcase_failure(message, message, details);
        }


        writer.end_testcase(modulename, testname, has_failures);
    }

    writer.end_testsuite(failures, testCount, timestamp, duration);
}

var onErrorXML = function(msg) {
    var testName = 'QUnit Timeout';
    var moduleName = "QUnit ";
    var timestamp = ISODateString(new Date());

    console.log('<?xml version="1.0"?>');
    console.log('<!--\n ' + msg + ' \n-->');
    console.log('<testsuite name="QUnit - JavaScript Tests" timestamp="'+ timestamp +'" tests="1" failures="1">');
    console.log('<testcase name="'+ testName +'" classname="'+ moduleName +'">');
    console.log('<failure message="'+ moduleName +'" type="'+ moduleName +'">');
    console.log(msg);
    console.log('</failure>');
    console.log('</testcase>');
    console.log('</testsuite>');
}

var onErrorText = function(msg) {
    console.log(msg);
}

if (phantom.args.length === 0 || phantom.args.length > 3) {
    console.log('Usage: run-qunit.js URL <TYPE> <SUITENAME>');
    console.log('TYPE: either text or junit-xml');
    phantom.exit();
}

var page = new WebPage();
var output = new Object();
output.type = phantom.args[1] || 'text';
output.suitename = phantom.args[2] || 'QUnit';
output.writer = ConsoleReportWriter;
output.onError = onErrorText;
if (output.type == 'xml') {
    output.writer  = JUnitXMLReportWriter;
    output.onError  = onErrorXML;
}

// Route "console.log()" calls from within the Page context to the main Phantom context (i.e. current "this")
page.onConsoleMessage = function(msg) {
    console.log(msg);
};

var firstCall;
page.open(phantom.args[0], function(status){
    //page.loads gets called multiple times when iframes are dynamically added, only allow 1st call to continue
    if (firstCall !== undefined) {
        return;
    }
    firstCall = false;
    if (status !== "success") {
        console.log("Unable to access network");
        phantom.exit();
    } else {
        waitFor(function(){
            return page.evaluate(function(){
                var el = document.getElementById('qunit-testresult');
                if (el && el.innerText.match('completed')) {
                    return true;
                }
                return false;
            });
        }, function(){
            var failedNum = page.evaluate(function(){
                var el = document.getElementById('qunit-testresult');
                try {
                    return el.getElementsByClassName('failed')[0].innerHTML;
                } catch (e) { }
                return 10000;
            });
            var result = page.evaluate(function(){
                return {
                    testresult: document.getElementById('qunit-testresult').innerText,
                    testresult_html: document.getElementById('qunit-testresult').innerHTML,
                    tests: document.getElementById('qunit-tests').innerText,
                    tests_html: document.getElementById('qunit-tests').innerHTML
                }
            });
            generate_report(output.suitename, result, output.writer);
            phantom.exit((parseInt(failedNum, 10) > 0) ? 1 : 0);

        },
                output.onError,
                60000); /*max. 60s for all tests */
    }});
