#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/energy-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/olsr-helper.h"
#include <iomanip>

using namespace ns3;

struct SimConfig {
  uint32_t numNodes;
  double nodeSpeed;
  double pauseTime;
  double areaSize;
  std::string trafficType;
  uint32_t packetSize;
  double txRange;
  double rxRange;
  double simTime;
  double trafficLoad;
};

SimConfig GenerateRandomConfig(uint32_t nodeCount) {
  SimConfig config;
  config.numNodes = nodeCount;
  config.nodeSpeed = std::vector<double>{1, 5, 10, 15, 20}[rand() % 5];
  config.pauseTime = rand() % 6;
  config.areaSize = 200 + rand() % 101;
  config.trafficType = "UDP";
  config.packetSize = 512 + (rand() % 4) * 128;
  config.txRange = 50.0 + rand() % 51;
  config.rxRange = 50.0 + rand() % 51;
  config.simTime = 15.0 + (rand() % 11);
  config.trafficLoad = rand() % 100 + 1;
  return config;
}

std::string GetPerformanceClass(double pdr, double throughput) {
  if (pdr > 0.8 && throughput > 500) return "High";
  if (pdr > 0.5 && throughput > 200) return "Medium";
  return "Low";
}

void RunSimulation(std::string protocol, int runId, std::ofstream &csv, SimConfig config) {
  std::cout << "Running simulation for config: "
            << "Nodes=" << config.numNodes
            << ", Speed=" << config.nodeSpeed
            << ", PacketSize=" << config.packetSize
            << ", SimTime=" << config.simTime
            << std::endl;

  SeedManager::SetSeed(12345);
  SeedManager::SetRun(runId);

  if (config.simTime < 2.0) config.simTime = 10.0;
  if (config.numNodes < 2) config.numNodes = 2;
  if (config.areaSize > 300.0) config.areaSize = 300.0;
  if (config.txRange < 50.0) config.txRange = 50.0;

  NodeContainer nodes;
  nodes.Create(config.numNodes);

  MobilityHelper mobility;
  Ptr<ListPositionAllocator> posAlloc = CreateObject<ListPositionAllocator>();
  Ptr<UniformRandomVariable> xRand = CreateObject<UniformRandomVariable>();
  Ptr<UniformRandomVariable> yRand = CreateObject<UniformRandomVariable>();

  for (uint32_t i = 0; i < config.numNodes; ++i) {
    posAlloc->Add(Vector(xRand->GetValue(0, config.areaSize), yRand->GetValue(0, config.areaSize), 0.0));
  }

  mobility.SetPositionAllocator(posAlloc);
  mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
  mobility.Install(nodes);

  WifiHelper wifi;
  wifi.SetStandard(WIFI_STANDARD_80211b);
  wifi.SetRemoteStationManager("ns3::AarfWifiManager");

  YansWifiChannelHelper channel = YansWifiChannelHelper::Default();
  YansWifiPhyHelper phy;
  phy.SetChannel(channel.Create());

  WifiMacHelper mac;
  mac.SetType("ns3::AdhocWifiMac");

  NetDeviceContainer devices = wifi.Install(phy, mac, nodes);

  InternetStackHelper stack;
  if (protocol == "OLSR") {
    OlsrHelper olsr;
    stack.SetRoutingHelper(olsr);
  }
  stack.Install(nodes);

  Ipv4AddressHelper address;
  address.SetBase("10.1.0.0", "255.255.0.0");
  Ipv4InterfaceContainer interfaces = address.Assign(devices);

  BasicEnergySourceHelper energy;
  energy.Set("BasicEnergySourceInitialEnergyJ", DoubleValue(100.0));
  ns3::energy::EnergySourceContainer sources = energy.Install(nodes);

  WifiRadioEnergyModelHelper radio;
  radio.Install(devices, sources);

  uint16_t port = 9;
  OnOffHelper onoff("ns3::UdpSocketFactory", InetSocketAddress(interfaces.GetAddress(1), port));
  onoff.SetConstantRate(DataRate("1Mbps"), config.packetSize);
  ApplicationContainer apps = onoff.Install(nodes.Get(0));
  apps.Start(Seconds(1.0));
  apps.Stop(Seconds(config.simTime));

  PacketSinkHelper sink("ns3::UdpSocketFactory", InetSocketAddress(Ipv4Address::GetAny(), port));
  ApplicationContainer sinkApps = sink.Install(nodes.Get(1));
  sinkApps.Start(Seconds(0.0));

  FlowMonitorHelper flowmon;
  Ptr<FlowMonitor> monitor = flowmon.InstallAll();

  Simulator::Stop(Seconds(config.simTime));
  Simulator::Run();

  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
  auto stats = monitor->GetFlowStats();

  double totalTx = 0, totalRx = 0, totalDelay = 0, totalLost = 0, throughput = 0;
  for (auto &flow : stats) {
    totalTx += flow.second.txPackets;
    totalRx += flow.second.rxPackets;
    totalLost += flow.second.lostPackets;
    totalDelay += flow.second.delaySum.GetMilliSeconds();
    double dur = flow.second.timeLastRxPacket.GetSeconds() - flow.second.timeFirstTxPacket.GetSeconds();
    if (dur > 0) {
      throughput += (flow.second.rxBytes * 8.0 / dur) / 1024.0;
    }
  }

  double totalPDR = totalTx > 0 ? totalRx / totalTx : 0;
  double avgDelay = totalRx > 0 ? totalDelay / totalRx : 0;

  double energyUsed = 0;
  for (uint32_t i = 0; i < sources.GetN(); ++i) {
    Ptr<ns3::energy::BasicEnergySource> src = DynamicCast<ns3::energy::BasicEnergySource>(sources.Get(i));
    energyUsed += 100.0 - src->GetRemainingEnergy();
  }

  std::string perfClass = GetPerformanceClass(totalPDR, throughput);

  csv << protocol << "," << config.numNodes << "," << config.nodeSpeed << ","
      << 0 << "," << 1 << "," << config.pauseTime << "," << config.areaSize << ","
      << config.trafficType << "," << config.packetSize << ","
      << config.txRange << "," << config.rxRange << ","
      << config.simTime << "," << config.trafficLoad << ","
      << std::fixed << std::setprecision(3) << totalPDR << ","
      << throughput << "," << avgDelay << "," << (totalLost / totalTx) << ","
      << stats.size() << "," << perfClass << "," << energyUsed << "\n";

  Simulator::Destroy();
}

int main(int argc, char *argv[]) {
  std::string protocol = "OLSR";   // ✅ Default is now OLSR
  CommandLine cmd;
  cmd.AddValue("protocol", "Routing protocol (OLSR)", protocol);
  cmd.Parse(argc, argv);

  std::ofstream csv("manet_dataset_" + protocol + ".csv");
  csv << "Protocol,NumNodes,NodeSpeed,Source,Destination,PauseTime,AreaSize,TrafficType,PacketSize,"
         "TxRange,RxRange,SimTime,TrafficLoad,PDR,Throughput (kbps),AvgDelay (ms),LossRate,"
         "RoutingOverhead,PerformanceClass,EnergyUsed (J)\n";

  std::vector<uint32_t> nodeCounts = {10, 20, 30, 40, 50};
  int runId = 0;
  for (auto count : nodeCounts) {
    for (int i = 0; i < 150; ++i) {
      SimConfig config = GenerateRandomConfig(count);
      RunSimulation(protocol, runId++, csv, config);
    }
  }

  csv.close();
  return 0;
}
