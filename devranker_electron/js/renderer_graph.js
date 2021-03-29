// Inter Process Communication(JS to Python Communication) ways - child_process, PythonShell & Flask. We used 'PythonShell'
// Ref: https://www.ahmedbouchefra.com/connect-python-3-electron-nodejs-build-desktop-apps/

try {
  // Logs from Node.js(console.log wont work in renderer.js as this is not associated with main process, but from Html Script Tag)  
  var nodeConsole = require('console');
  const { type } = require('os');
  const { ipcRenderer } = require('electron')
  var myConsole = new nodeConsole.Console(process.stdout, process.stderr);
  let pythonFileName = './py/devranker_functions.py'


  // Dictionary which is holding entire data from csv
  var dict_emails = {}

  // Initializing Selector(Dropdown) related variables
  let list_authors = []
  let list_languages = []

  // To store selected Language name 
  var str_selected_language = ''


  let list_selected_authors = ['All']

  // Initializing Graph related variables
  let list_x_axis_months = ["Jan", "Feb", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  let list_graph_dataset = []




  // Instances for widgets
  var ctx_for_linechart = document.getElementById("chart_line_area");
  var ctx_for_piechart = document.getElementById("chart_pie_area");


  // Setting default Year & Month to From & To Date pickers
  date_today = new Date()
  myConsole.log(new Date().getFullYear(), new Date().getMonth())
  input_from_month_and_year.defaultValue = date_today.getFullYear() - 1 + "-" + date_today.getUTCMonth() + 1;
  input_to_month_and_year.defaultValue = date_today.getFullYear() + "-" + date_today.getMonth() + 1;

  // Loading Line Graph with 'Chart.js'
  function loadLineGraph() {
    try {
      ctx_for_piechart.style.display = "none"
      ctx_for_linechart.style.display = 'block'

      new Chart(chart_line_area, {
        type: "line",
        data: {
          labels: list_x_axis_months,
          datasets: list_graph_dataset,
        },
        options: {
          scales: {
            xAxes: [{
              display: true,
              scaleLabel: {
                display: true,
                labelString: 'Month'
              }
            }],
            yAxes: [{
              display: true,
              scaleLabel: {
                display: true,
                labelString: 'Mod Score'
              },
              ticks: {
                beginAtZero: true,
              },
            }]
          },
          elements: {
            point: {
              pointStyle: 'rectRot'
            }
          }
        },
      });

    } catch (err) {
      alert(err)
    }
  }

  // Loading Pie Chart Graph
  function loadPieGraph() {


    myConsole.log('\n\nLoading pie Chart::\n')

    try {

      let list_mods_sum = []

      // Preparing Mods Total for Authors
      for (x in list_graph_dataset) {

        myConsole.log('\n\n\n\nAuthor:, ', list_authors[x], "::\n", list_graph_dataset[x])
        myConsole.log('ModScores:', "::\n", list_graph_dataset[x].data)

        let temp = 0

        for (y in list_graph_dataset[x].data) {
          temp = temp + parseInt(list_graph_dataset[x].data[y])
        }

        list_mods_sum.push("" + temp)

        temp = 0

        myConsole.log('Mods Total for Author, ', list_authors[x], " is::", temp) // , "\n\nPieChartList is::", list_mods_sum)
      }

      // Preparing Background colors for each Mod Total of Author
      list_bg_colors = []
      for (x in list_authors) {
        var rgbVals = randomRGB();
        let bg_color = "rgb(" + rgbVals[0] + ", " + rgbVals[1] + ", " + rgbVals[2] + ")"
        list_bg_colors.push(bg_color)
      }

      // Managing Visibility of canvas of line & pie charts
      myConsole.log('\n\n\n Pie Chart Data after Added Mod Scores for idividual Authores is::', list_mods_sum)
      ctx_for_linechart.style.display = "none"
      ctx_for_piechart.style.display = 'block'

      // Preparing Config
      var config = {
        type: 'pie',
        data: {
          datasets: [{
            data: list_mods_sum,
            backgroundColor: list_bg_colors,
            label: 'Dataset 1'
          }],
          labels: list_authors
        },
        options: {
          responsive: true
        }
      };

      new Chart(chart_pie_area, config);

    } catch (err) {
      alert(err)
    }
  }

  // Preparing Idividual Author's Data to add for Graph Dataset i.e, 'list_graph_dataset'
  // 'name' is Label Name & 'array_mods' is y-Axis values for 12 months(For X-Axis)
  function get_graph_dataset_obj(name, array_mods) {

    var rgbVals = randomRGB();
    var rgbVals_2 = randomRGB();

    let bg_color = "rgb(" + rgbVals[0] + ", " + rgbVals[1] + ", " + rgbVals[2] + ")"
    let b_color = "rgb(" + rgbVals_2[0] + ", " + rgbVals_2[1] + ", " + rgbVals_2[2] + ")"

    return {
      label: name,
      fill: false,
      data: array_mods,
      backgroundColor: bg_color,
      borderColor: bg_color,
      pointRadius: 10,
      pointHoverRadius: 15,
      borderWidth: 1,
    }
  }

  // To Generate Random RGB Values, which is required to generate Random Colors for Graph Line Background & Border
  function randomRGB() {
    var red = randomNum();
    var green = randomNum();
    var blue = randomNum();
    return [red, green, blue];
  }

  function randomNum() {
    return Math.floor(Math.random() * 256);
  }

  // Appending data to Selectors(Dropdowns). i.e, Author Email & Language
  function setSelectors() {

    list_authors = Object.keys(dict_emails)
    list_authors_data = Object.values(dict_emails)

    myConsole.log("list_authors_data:\n", list_authors_data)

    for (var x in list_authors) {
      select_emails.options[select_emails.options.length] = new Option(list_authors[x], x);
    }

    // Languages
    // Adding Languages Data(file_ext) in 'list_languages' variable
    for (var x in list_authors_data) {

      for (var y in list_authors_data[x]) {
        var language = list_authors_data[x][y].file_ext
        let array_lang_splitted = language.split(",")

        // myConsole.log("language::\n", language, "\ntype::\n", typeof (language), "\narray_lang_splitted::\n", array_lang_splitted)
        for (var z in array_lang_splitted) {
          // Checking if same name added already, if not then only adding it to list 'list_languages'
          if (!list_languages.includes(array_lang_splitted[z]) && array_lang_splitted[z] != "") {
            list_languages.push(array_lang_splitted[z])
          }
        }
      }
    }

    myConsole.log("list_languages:\n", list_languages)


    // Binding languages to dropdown
    for (var x in list_languages) {
      select_languages.options[select_languages.options.length] = new Option(list_languages[x], x);
    }


    // On Author Email Selected
    select_emails.onchange = function () {
      list_selected_authors = [];
      for (var option of select_emails.options) {
        if (option.selected) {
          list_selected_authors.push(option.value);
        }
      }
      myConsole.log('Selected Author Indexes::', list_selected_authors)
    }

    // On Language Selected
    select_languages.onchange = function () {
      myConsole.log(this.value)
      myConsole.log('Selected Language Index::', this.value, list_languages[this.value])
      if (this.value != undefined) {
        str_selected_language = list_languages[this.value]
      } else {
        str_selected_language = ""
      }
    }
  }

  function prepareGraphData(isLineGraph) {

    try {
      // Validating for Language
      if (str_selected_language == "") {
        alert('Please select Language')
        return
      }

      // Getting Selected Month & Year values V
      let arr_splitted_from_date = (input_from_month_and_year.value).split("-")
      let arr_splitted_to_date = (input_to_month_and_year.value).split("-")

      let from_year = arr_splitted_from_date[0];
      let from_month = arr_splitted_from_date[1];

      let to_year = arr_splitted_to_date[0];
      let to_month = arr_splitted_to_date[1];

      // Validating Selected Month & Year
      // (0 - Same Year) || (-1 - Correct Diff, From month > To Month)-> 
      // parseInt - To convert String into Integer
      if ((parseInt(from_year) - parseInt(to_year) == 0) || (parseInt(from_year) - parseInt(to_year) == -1 && parseInt(from_month) >= parseInt(to_month))) {
        list_graph_dataset = []
      } else {
        alert("From & To Dates Interval must be 12 months")
        return
      }

      // 'list_authors' & 'list_authors_data' were already initialized in 'setSelectors()' from 'dict_emails' main dictionary
      for (x in list_authors) {

        if (list_selected_authors.includes(x) || list_selected_authors.includes('All')) {

          // Initializing 12 months Data as 0's for all authors
          let list_mods_of_all_months = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

          // Separating Date & Modscore-file_ext from 'list_authors_data' which was separated already from main dictionary 'dict_emails'
          let __list_cur_author_dates = Object.keys(list_authors_data[x])
          let __list_cur_author_score_and_file_ext = Object.values(list_authors_data[x])

          for (y in __list_cur_author_dates) {

            let date = new Date(__list_cur_author_dates[y])

            let data_month = date.getUTCMonth() + 1
            let data_year = date.getUTCFullYear()

            // Validating with 'From' & 'To' month-year
            if (from_year <= data_year && to_year >= data_year) {
              // Updating mod score by adding it to current mod for that month
              // Existing value + Current value, here -1 is for index
              // myConsole.log('month is :', data_month, "Its mod Value is:", list_values[y], "Present Mod value of month ", list_mods_of_all_months)

              myConsole.log('\n\nChecking Language::\n-', str_selected_language, "==?", __list_cur_author_score_and_file_ext[y].file_ext,)
              // Checking Language is selected Language or not, then only adding mod score
              if (__list_cur_author_score_and_file_ext[y].file_ext.includes(str_selected_language)) {
                let updated_mod_value = list_mods_of_all_months[data_month - 1] + __list_cur_author_score_and_file_ext[y].mod_score
                // Updating existing value in list 'list_mods_of_all_months' by considering index as 'data_month'
                list_mods_of_all_months.splice(data_month - 1, 1, updated_mod_value)
                // myConsole.log(list_mods_of_all_months)
              }
            }
          }
          myConsole.log("\n\nModsList of '", list_authors[x], "is :: \n", list_mods_of_all_months)
          list_graph_dataset.push(get_graph_dataset_obj(list_authors[x], list_mods_of_all_months))
        }
      }
    } catch (err) {
      myConsole.log("btn_clicked::exception::", err)
      alert(err)
    }

    // myConsole.log("list_graph_dataset::", list_graph_dataset)
    // Till now prepared Dataset, Loading Graph now
    if (isLineGraph) {
      loadLineGraph()
    } else {
      loadPieGraph()
    }
  }

  // On Clicking 'Load Line Chart' button
  btn_load_line.addEventListener('click', () => {
    prepareGraphData(true)
  });

  // On Clicking 'Load Pie Chart' button
  btn_load_pie.addEventListener('click', () => {
    prepareGraphData(false)
  });


  btn_back.addEventListener('click', () => {
    const { remote } = require('electron')
    // remote.getCurrentWindow().back()
    // window.history.back();
    remote.getCurrentWindow().loadFile('./html/home.html')
    // history.go(-1)
  })


  // Get File Path from 'main.js' through Synchronous Communication in IPC
  let pathInfo = ipcRenderer.sendSync('synchronous-getPathInfo', 'get pathInfo')
  myConsole.log('\n\nrenderer_graph.js::synchronous-getPathInfo::', pathInfo)

  if (pathInfo != undefined) {

    const fs = require('fs');
    const papa = require('papaparse');
    const file = fs.createReadStream(pathInfo.de_anonymized_file_path);

    papa.parse(file, {
      worker: false, // To run in Main thread if file is Longer, but as this .js file is renderer here we cant use it.So always 'false', otherwise it will throw exception
      header: true,
      step: function (result) {

        try {

          myConsole.log('parsing result::\n', result);

          let _date = result.data.committed_date
          let _email = result.data.Email
          let _modscore = result.data.mod_score
          var _file_ext = result.data.file_ext

          // Checking for undefineed o 'NoExt'
          if (_file_ext == undefined || _file_ext == 'NoExt') {
            // To avoid adding 'undefined' unnecessarily while adding first time
            _file_ext = ""
          }

          // Sometimes getting Unwanted Spaces either at Starting or Ending. So trimming
          _file_ext = _file_ext.trim()

          // If 'Email' not yet existing, then adding it
          if (!dict_emails.hasOwnProperty(result.data.Email)) {
            dict_emails[_email] = { [_date]: { mod_score: _modscore, file_ext: _file_ext } }
          } else {
            // So Email exists already
            let value_for_email = dict_emails[_email]
            // Checking if current date already existing
            // If Date not added then add now as Value
            if (!value_for_email.hasOwnProperty(_date)) {
              dict_emails[_email][_date] = { mod_score: _modscore, file_ext: _file_ext }
            } else {
              let value_for_date = value_for_email[_date]
              // If Date already added, update modscore & file_ext
              dict_emails[_email][_date].mod_score = parseInt(value_for_date.mod_score) + parseInt(_modscore)

              if (dict_emails[_email][_date].file_ext != "") {
                dict_emails[_email][_date].file_ext = value_for_date.file_ext + ',' + _file_ext
              }
            }
          }
        } catch (err) {
          alert(err)
        }
      },
      complete: function (results, file) {
        id_loader.style.display = "none"
        myConsole.log(dict_emails)
        setSelectors()
      }
    });

  } else {
    alert('Unable to fetch De-Anonymized file path')
  }
} catch (err) {
  alert(err)
}