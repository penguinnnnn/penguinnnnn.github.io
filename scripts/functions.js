function toggleblock(blockId)
{
   var block = document.getElementById(blockId);
   if (block.style.display == 'none') {
    block.style.display = 'block' ;
   } else {
    block.style.display = 'none' ;
   }
}

/* Reorder an element's children in place, Fisher-Yates.
   Called inline right after the gallery so it runs while the page is still
   parsing -- the shuffled order is what gets painted, with no visible jump. */
function shuffleChildren(blockId)
{
   var block = document.getElementById(blockId);
   if (!block) { return; }
   var kids = Array.prototype.slice.call(block.children);
   for (var i = kids.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var tmp = kids[i]; kids[i] = kids[j]; kids[j] = tmp;
   }
   var frag = document.createDocumentFragment();
   for (var k = 0; k < kids.length; k++) { frag.appendChild(kids[k]); }
   block.appendChild(frag);
}
