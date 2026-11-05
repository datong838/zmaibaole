import Foundation
import Vision
import ImageIO
import CoreGraphics
let started=ProcessInfo.processInfo.systemUptime
func need(_ ok:Bool,_ message:String) throws { if !ok {throw NSError(domain:message,code:1)} }
do {
 let args=CommandLine.arguments
 try need(args.count==3,"image-and-plan-required")
 let plan=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:args[2]))) as! [String:Any]
 let source=CGImageSourceCreateWithURL(URL(fileURLWithPath:args[1]) as CFURL,nil)!
 let image=CGImageSourceCreateImageAtIndex(source,0,nil)!
 var results=[[String:Any]]()
 for cell in plan["cells"] as! [[String:Any]] {
  let b=cell["box"] as! [Int]
  try need(b.count==4 && b[0]>=0 && b[1]>=0 && b[2]<=image.width && b[3]<=image.height && b[0]<b[2] && b[1]<b[3],"cell-outside-image")
  let crop=image.cropping(to:CGRect(x:b[0],y:b[1],width:b[2]-b[0],height:b[3]-b[1]))!
  let request=VNRecognizeTextRequest()
  request.recognitionLevel = .accurate;request.recognitionLanguages=["zh-Hans","en-US"]
  request.usesLanguageCorrection=false;request.usesCPUOnly=true
  try VNImageRequestHandler(cgImage:crop,options:[:]).perform([request])
  let observations=(request.results ?? []).compactMap { o -> [String:Any]? in
   guard let v=o.topCandidates(1).first else{return nil};let b=o.boundingBox
   return ["text":v.string,"confidence":v.confidence,"box":[b.minX,b.minY,b.width,b.height]]
  }
  results.append(["key":cell["key"]!,"box":b,"observations":observations])
 }
 let out:[String:Any]=["kind":"local-vision-cell-ocr-v1","recognition_level":"accurate","recognition_languages":["zh-Hans","en-US"],"language_correction":false,"CPU_only":true,"cells":results,"elapsed_seconds":ProcessInfo.processInfo.systemUptime-started]
 let data=try JSONSerialization.data(withJSONObject:out,options:[.sortedKeys]);FileHandle.standardOutput.write(data)
} catch {FileHandle.standardError.write(Data(String(describing:error).utf8));exit(2)}
