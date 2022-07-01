autowatch = 1;

var maxsize = 3;
var fifo = new Array();
var counter = 0;

function loadbang ()
{
	clear();
}

function clear ()
{
	fifo = new Array();
	counter = 0;
	tocomment();
}
	
function anything ()
{
  var a = arrayfromargs(messagename, arguments);
	
  // prepend input count to list to store
  fifo.push([counter + ":"].concat(a));
  counter++;

  if (fifo.length > maxsize)
  {
    fifo.shift();
  }	

  tocomment();
}

function bang ()
{
	fifo.forEach(function(f) 
	{
		//post(f, "\n");
		outlet(0, f);
	});
}

// fill a comment obj
function tocomment ()
{
	outlet(0, "set");
	fifo.forEach(function(f) 
	{
		//post(f, "\n");

		// the comment obj would eat the spaces, so we
		// convert list to string (uses commas, DUH!), then replace commas
		f = f.toString().replace(/,/g, " ");
 
		outlet(0, "append", f, "\n");
	});
}

if (jsarguments.length > 1)
{
  maxsize = jsarguments[1];
}
