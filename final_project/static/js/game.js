document.addEventListener('DOMContentLoaded', () => {
  var dropzone = document.getElementById('dropzone');
  var dropzone_sortable = Sortable.create(dropzone, {group: "words", animation: 150, onAdd: set_input_value, onUpdate: set_input_value, onRemove: set_input_value});
  var bottom_words = document.getElementById('bottom_words');
  var bottom_sortable = Sortable.create(bottom_words, {group: "words", animation: 150, onAdd: set_input_value, onUpdate: set_input_value, onRemove: set_input_value});

  var guess_inputA = document.getElementById('guess_inputA');
  var guess_inputB = document.getElementById('guess_inputB');
  var bottom_inputA = document.getElementById('bottom_inputA');
  var bottom_inputB = document.getElementById('bottom_inputB');
  function set_input_value(){
    let v = ""

    if (dropzone.children.length > 0) {
      for (let el of dropzone.children){
        v += `${el.textContent}🀄`
      }
    }

    if (guess_inputA != null) guess_inputA.value = v
    if (guess_inputB != null) guess_inputB.value = v

    set_bottom_value()
  }
  set_input_value()

  function set_bottom_value(){
    let v = ""

    if (bottom_words.children.length > 0) {
      for (let el of bottom_words.children){
        v += `${el.textContent}🀄`
      }
    }

    if (bottom_inputA != null) bottom_inputA.value = v
    if (bottom_inputB != null) bottom_inputB.value = v
  }
  set_bottom_value()

  shuffle_button = document.getElementById('shuffle_button');
  shuffle_button.addEventListener("click", shuffle_words)
  function shuffle_words(){
    var order = bottom_sortable.toArray();
    bottom_sortable.sort(knuthShuffle(order), true);
    set_input_value()
  }
})

//from rosetta code
function knuthShuffle(arr) {
    var rand, temp, i;

    for (i = arr.length - 1; i > 0; i -= 1) {
        rand = Math.floor((i + 1) * Math.random());//get random between zero and i (inclusive)
        temp = arr[rand];
        arr[rand] = arr[i]; //swap i (last element) with random element.
        arr[i] = temp;
    }
    return arr;
}
