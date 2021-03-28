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

        let temp = 0

        for (y in list_graph_dataset[x].data) {
          temp = temp + parseFloat(list_graph_dataset[x].data[y])
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

    try {
      list_authors = Object.keys(dict_emails)
      list_authors_data = Object.values(dict_emails)

      for (var x in list_authors) {
        select_emails.options[select_emails.options.length] = new Option(list_authors[x], x);
      }

      for (var x in list_authors_data) {

        let each_auth_info_obj = list_authors_data[x]
        var array_keys_for_languages = Object.values(each_auth_info_obj)

        for (var y in array_keys_for_languages) {
          // Array of Language Dict
          var array__languages = Object.keys(array_keys_for_languages[y])

          for (var w in array__languages) {
            // Checking if same name added already, if not then only adding it to list 'list_languages'
            if (!list_languages.includes(array__languages[w]) && array__languages[w] != "") {
              list_languages.push(array__languages[w])
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
        // myConsole.log('Selected Author Indexes::', list_selected_authors)
      }

      // On Language Selected
      select_languages.onchange = function () {
        // myConsole.log(this.value)
        // myConsole.log('Selected Language Index::', this.value, list_languages[this.value])
        if (this.value != undefined) {
          str_selected_language = list_languages[this.value]
        } else {
          str_selected_language = ""
        }
      }
    } catch (err) {
      alert(err)
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

        // Validation - x & list_selected_authors are indexs for Authors so comparing
        if (list_selected_authors.includes(x) || list_selected_authors.includes('All')) {

          // list_authors_data[x] is current author's data
          // list_authors[x] - 12 months Data initially 0
          let list_mods_of_all_months = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


          // List of Dates
          let __list_keys_list_authors_data = Object.keys(list_authors_data[x]) // Dates

          // List of Dict of Language & Modscore
          let __list_values_list_authors_data = Object.values(list_authors_data[x]) // File ext & Modscore

          for (y in __list_keys_list_authors_data) {

            let date = new Date(__list_keys_list_authors_data[y])

            let data_month = date.getUTCMonth() + 1
            let data_year = date.getUTCFullYear()

            // Validating with 'From' & 'To' month-year
            if (from_year <= data_year && to_year >= data_year) {

              // Value of date key (Dictionary)
              let dict_of_current_date = __list_values_list_authors_data[y]

              if (dict_of_current_date.hasOwnProperty(str_selected_language)) {

                let updated_mod_value = list_mods_of_all_months[data_month - 1] + dict_of_current_date[str_selected_language]

                // Updating existing value in list 'list_mods_of_all_months' by considering index as 'data_month'
                list_mods_of_all_months.splice(data_month - 1, 1, updated_mod_value)
              }
            }
          }
          myConsole.log('\n\n\n ModScores for ', list_authors[x], ' is:\n', list_mods_of_all_months)
          list_graph_dataset.push(get_graph_dataset_obj(list_authors[x], list_mods_of_all_months))
        }
      }
    } catch (err) {
      myConsole.log("btn_clicked::exception::", err)
      alert(err)
    }

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
          // myConsole.log('parsing result::\n', result);
          let _date = result.data.committed_date.split(" ")[0]
          let _email = result.data.Email

          let _modscore = parseFloat(result.data.mod_score)

          var _file_ext = result.data.file_ext
          var _language_supported = result.data.language_supported // dont forgot, its a string value

          // Ravi: If dont want to add Authors if 'language_supported == False'
          if (!isNaN(_modscore) && _file_ext != undefined && _file_ext != "" && _file_ext != 'NoExt' && _language_supported == 'True') {

            // Ravi: Including All authors who had 'language_supported == False'
            // if (!isNaN(_modscore) && _file_ext != undefined && _file_ext != "" && _file_ext != 'NoExt') {

            // EMAIL - not availabe?
            if (!dict_emails.hasOwnProperty(result.data.Email)) {
              // Creating Email & Date dictionaries
              dict_emails[_email] = {}
              dict_emails[_email][_date] = {}

              // If File Extension is Empty, then leave it.
              if (_file_ext != "") {
                dict_emails[_email][_date][_file_ext] = _modscore
              }

              // EMAIL avaialble
            } else {

              let value_for_email = dict_emails[_email]

              // DATE - not availabe?
              if (!value_for_email.hasOwnProperty(_date)) {

                dict_emails[_email][_date] = {}

                // If File Extension is not Empty, then leave it.
                if (_file_ext != "") {
                  dict_emails[_email][_date][_file_ext] = _modscore
                }
                // DATE - availabe?
              } else {

                let value_for_date = value_for_email[_date]

                // If File ext not available
                if (!value_for_date.hasOwnProperty(_file_ext)) {
                  dict_emails[_email][_date][_file_ext] = _modscore
                } else {
                  let presentvalue = parseFloat(dict_emails[_email][_date][_file_ext])

                  if (!isNaN(presentvalue)) {
                    dict_emails[_email][_date][_file_ext] = _modscore + presentvalue
                  }
                }
              }
            }
          }
        } catch (err) {
          alert(err)
        }
      },
      complete: function (results, file) {
        setSelectors()
        id_loader.style.display = "none"
        myConsole.log("dict_emails::", dict_emails)
      }
    });

  } else {
    alert('Unable to fetch De-Anonymized file path')
  }
} catch (err) {
  alert(err)
}