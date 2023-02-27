const rp = require('request-promise')
const getOptions = {
  uri: 'https://api.app.shortcut.com/api/v2/search/stories',
  json: true,
  qs: {
    token: 'xxx', // API token
    query: 'project:50 state:500000044' // Target the stories you care about
  },
}

const putOptions = {
  method: 'PUT',
  uri: '',
  qs: {
    token: 'xxx' // API token
  },
  body: {},
  json: true
}

rp(getOptions).then((searchResults) => { // Get stories using request-promise.
  const stories = searchResults.data

  // Sort stories by deadline (due date) field.
  stories.sort((a, b) => {
    if (!a.deadline) return 1 // Put stories with no deadlines later
    if (!b.deadline) return -1
    return a.deadline < b.deadline ? -1 : 1
  })

  // Send priority order updates to Shortcut. Wait for each call to finish before going to the next one.
  async function sendPriorityOrderUpdates() {
    for (let i = 1; i < stories.length; i++) {
      putOptions.uri = 'https://api.app.shortcut.com/api/v2/stories/' + stories[i].id
      putOptions.body.after_id = stories[i - 1].id
      await rp(putOptions)
    }
  }
  sendPriorityOrderUpdates()

}).catch((error) => {
  console.log(error)
})
