<?php
include("../../config/settings.inc.php");
include("../../include/database.inc.php");

$year = isset($_GET["year"]) ? $_GET["year"] : date("Y");
$month = isset($_GET["month"]) ? $_GET["month"] : date("m");
$day = isset($_GET["day"]) ? $_GET["day"] : date("d");
$station = isset($_GET["station"]) ? $_GET["station"]: "OT0002";

$myTime = mktime(0,0,0,$month, $day, $year);

$dirRef = strftime("%Y_%m/%d", $myTime);
$titleDate = strftime("%b %d, %Y", $myTime);

$db = iemdb("other");
$sql = sprintf("SELECT * from t%s WHERE station = '%s' and date(valid) = '%s' ORDER by valid ASC", $year, $station, strftime("%Y-%m-%d", $myTime) );

$drct = array();
$sknt = array();
$times = array();

$rs = pg_exec($db, $sql);

for($i=0; $row = @pg_fetch_array($rs,$i); $i++){
  $sknt[] = $row["sknt"];
  $drct[] = $row["drct"];
  $times[] = strtotime( $row["valid"] );

} // End of while

include ("../../include/jpgraph/jpgraph.php");
include ("../../include/jpgraph/jpgraph_line.php");
include ("../../include/jpgraph/jpgraph_date.php");

// Create the graph. These two calls are always required
$graph = new Graph(600,300);
$graph->SetScale("datelin");
$graph->SetY2Scale("lin",0,360);

$graph->img->SetMargin(65,40,45,60);
//$graph->xaxis->SetFont(FONT1,FS_BOLD);
//$graph->xaxis->SetTextLabelInterval(60);

$graph->xaxis->SetLabelAngle(90);
$graph->yaxis->scale->ticks->Set(2,1);
//$graph->yscale->SetGrace(10);
$graph->title->Set("Winds");
$graph->subtitle->Set($titleDate );

$graph->legend->SetLayout(LEGEND_HOR);
$graph->legend->Pos(0.01,0.075);

//[DMF]$graph->y2axis->scale->ticks->Set(100,25);

$graph->title->SetFont(FF_FONT1,FS_BOLD,14);
$graph->yaxis->SetTitle("Wind Speed [knots]");

//[DMF]$graph->y2axis->SetTitle("Solar Radiation [W m**-2]");

$graph->yaxis->title->SetFont(FF_FONT1,FS_BOLD,12);
$graph->xaxis->SetTitle("Valid Local Time");
$graph->xaxis->SetTitleMargin(30);
//$graph->yaxis->SetTitleMargin(48);
$graph->yaxis->SetTitleMargin(40);
$graph->xaxis->title->SetFont(FF_FONT1,FS_BOLD,12);
$graph->xaxis->SetPos("min");

// Create the linear plot
if (max($drct) > 0){
 $lineplot=new LinePlot($drct, $times);
 $lineplot->SetLegend("Direction");
 $lineplot->SetColor("blue");
 $graph->AddY2($lineplot);
}

// Create the linear plot
if (max($sknt) > 0){
 $lineplot2=new LinePlot($sknt, $times);
 $lineplot2->SetLegend("Speed [kts]");
 $lineplot2->SetColor("red");
 $graph->Add($lineplot2);
}

$graph->Stroke();

?>
