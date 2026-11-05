#import <Cocoa/Cocoa.h>
#import <ApplicationServices/ApplicationServices.h>
#import <CoreGraphics/CoreGraphics.h>
#include <unistd.h>
#include <sys/file.h>
#include <fcntl.h>
static BOOL save(NSString *path, NSDictionary *value) {
 NSData *d=[NSJSONSerialization dataWithJSONObject:value options:NSJSONWritingPrettyPrinted error:nil];
 return d && [d writeToFile:path options:NSDataWritingAtomic error:nil];
}
static NSDictionary *permissions(void) {
 return @{ @"accessibility":@(AXIsProcessTrusted()), @"screen_capture":@(CGPreflightScreenCaptureAccess()) };
}
static BOOL ready(NSDictionary *p) { return [p[@"accessibility"] boolValue] && [p[@"screen_capture"] boolValue]; }

static NSDictionary *settings(void){
 NSString *p=[[NSBundle mainBundle] pathForResource:@"host-config" ofType:@"json"];
 NSData *d=p?[NSData dataWithContentsOfFile:p]:nil;id c=d?[NSJSONSerialization JSONObjectWithData:d options:0 error:nil]:nil;
 if(![c isKindOfClass:[NSDictionary class]])return nil;
 for(NSString *k in @[@"python",@"probe_file",@"probe_dir",@"package",@"root",@"app_path"])if(![c[k] isKindOfClass:[NSString class]]||![c[k] isAbsolutePath])return nil;
 if(![c[@"probe_file"] isEqualToString:[[NSHomeDirectory() stringByAppendingPathComponent:@"Downloads"] stringByAppendingPathComponent:c[@"probe_filename"]]])return nil;
 if(![c[@"app_path"] isEqualToString:[[NSBundle mainBundle] bundlePath]])return nil;
 if(![[NSFileManager defaultManager] fileExistsAtPath:[c[@"root"] stringByAppendingPathComponent:@"config.json"]])return nil;
 return c;
}
static int probe(NSDictionary *c);
static int serve(NSDictionary *c) {
 NSString *lock=[c[@"root"] stringByAppendingPathComponent:@"authorization-host.lock"];
 int fd=open(lock.fileSystemRepresentation,O_CREAT|O_RDWR,0600);
 if(fd<0 || flock(fd,LOCK_EX|LOCK_NB)!=0) return 73;
 NSString *out=[c[@"root"] stringByAppendingPathComponent:@"authorization-host.json"];
 int childPermissionRC=probe(c);
 if(childPermissionRC!=0){
  if(!save(out,@{@"kind":@"workshop-host-permission-handoff-v3",@"state":@"waiting-child-system-authorization",@"child_probe_exit":@(childPermissionRC),@"scheduler_spawned":@NO,@"probe_index":[c[@"probe_dir"] stringByAppendingPathComponent:@"latest.json"],@"action":@"Use the visible permission window, inspect preserved child receipts, then explicitly restart this host only after quiescent supervisor review."}))return 74;
  while(1)sleep(30); // No background repeated probes, no scheduler or automatic task retry.
 }
 while(1) {
  NSDictionary *p=permissions();
  if(!ready(p)) {
   if(!save(out,@{@"kind":@"workshop-host-permission-handoff-v1",@"state":@"waiting-system-authorization",@"permissions":p,@"worker_spawned":@NO,@"pid":@(getpid()),@"observed_at":@([[NSDate date] timeIntervalSince1970]),@"action":@"Open this signed app normally; grant Accessibility and Screen Recording in System Settings. Child authorization must be verified before resuming tasks."})) return 74;
   sleep(30); continue;
  }
  NSTask *t=[NSTask new]; t.executableURL=[NSURL fileURLWithPath:c[@"python"]];
  t.arguments=@[@"-m",@"workshop_director",@"--root",c[@"root"],@"serve"];
  NSMutableDictionary *env=[[[NSProcessInfo processInfo] environment] mutableCopy]; env[@"PYTHONPATH"]=c[@"package"];t.environment=env;t.currentDirectoryURL=[NSURL fileURLWithPath:c[@"root"]];
  NSError *error=nil;
  if(![t launchAndReturnError:&error]) {save(out,@{@"kind":@"workshop-host-status-v1",@"state":@"spawn-failed",@"error":error.localizedDescription?:@"unknown"});return 75;}
  save(out,@{@"kind":@"workshop-host-status-v1",@"state":@"scheduler-child-started",@"host_pid":@(getpid()),@"child_pid":@(t.processIdentifier),@"permissions":p,@"child_permission_inheritance_verified":@YES,@"permission_probe_index":[c[@"probe_dir"] stringByAppendingPathComponent:@"latest.json"]});
  [t waitUntilExit];
  save(out,@{@"kind":@"workshop-host-status-v1",@"state":@"scheduler-child-exited",@"exit_code":@(t.terminationStatus),@"termination_reason":@(t.terminationReason)});
  close(fd);return t.terminationStatus;
 }
}

static int probe(NSDictionary *c){
 // No shell/environment PYTHONPATH imports; only this sealed standard-library script.
 NSTask *t=[NSTask new];t.executableURL=[NSURL fileURLWithPath:c[@"python"]];
 t.arguments=@[@"-I",[[NSBundle mainBundle] pathForResource:@"permission_probe" ofType:@"py"],@"--config",[[NSBundle mainBundle] pathForResource:@"host-config" ofType:@"json"],@"--host-pid",[@(getpid()) stringValue]];
 NSPipe *pipe=[NSPipe pipe];t.standardOutput=pipe;t.standardError=[NSFileHandle fileHandleWithStandardError];NSError *error=nil;
 if(![t launchAndReturnError:&error]){fprintf(stderr,"child-probe-spawn-failed\n");return 75;}
 NSData *d=[[pipe fileHandleForReading] readDataToEndOfFile];[t waitUntilExit];
 id r=[NSJSONSerialization JSONObjectWithData:d options:0 error:nil];
 if(![r isKindOfClass:[NSDictionary class]]||![r[@"kind"] isEqual:@"workshop-child-permission-probe-v1"]){fprintf(stderr,"child-probe-invalid-result\n");return 76;}
 // Every read-only probe has a fresh immutable receipt; failed grants can be checked again.
 NSString *out=[c[@"probe_dir"] stringByAppendingPathComponent:[NSString stringWithFormat:@"probe-%@.json",[[NSUUID UUID] UUIDString]]];
 if(![d writeToFile:out options:NSDataWritingWithoutOverwriting error:&error])return 74;
 if(!save([c[@"probe_dir"] stringByAppendingPathComponent:@"latest.json"],@{@"receipt_path":out,@"host_pid":@(getpid()),@"child_pid":@(t.processIdentifier),@"exit_code":@(t.terminationStatus),@"app_path":[[NSBundle mainBundle] bundlePath],@"observed_at":@([[NSDate date] timeIntervalSince1970])}))return 74;
 fwrite(d.bytes,1,d.length,stdout);return t.terminationStatus;
}
static void downloads(NSDictionary *c){
 NSOpenPanel *p=[NSOpenPanel openPanel];p.canChooseDirectories=YES;p.canChooseFiles=NO;p.allowsMultipleSelection=NO;p.directoryURL=[NSURL fileURLWithPath:[NSHomeDirectory() stringByAppendingPathComponent:@"Downloads"]];p.message=@"请选择您的 Downloads（下载）目录，仅用于读取本次已导出的 Excel；不需要完全磁盘访问。";
 if([p runModal]!=NSModalResponseOK)return;
 NSURL *url=p.URL;
 if(![[url.path stringByStandardizingPath] isEqualToString:[NSHomeDirectory() stringByAppendingPathComponent:@"Downloads"]])return;
 BOOL scoped=[url startAccessingSecurityScopedResource];
 // User action only: open exactly the pinned export; no listing, parsing or write.
 NSFileHandle *h=[NSFileHandle fileHandleForReadingFromURL:[NSURL fileURLWithPath:c[@"probe_file"]] error:nil];
 BOOL readable=h!=nil;if(h)[h closeFile];if(scoped)[url stopAccessingSecurityScopedResource];
 NSAlert *a=[NSAlert new];a.messageText=readable?@"当前应用可打开指定下载文件":@"下载文件仍不可读取";a.informativeText=@"这不代表子 Python 已有权限。请执行窗口中的子进程权限检查。若系统拒绝，请在隐私与安全性→文件与文件夹中允许本应用访问下载文件夹；无需完全磁盘访问。";[a runModal];
}
int main(int argc,const char **argv){@autoreleasepool{
 if(argc==2&&!strcmp(argv[1],"--help")){puts("WorkshopHost --permissions | --probe-child | --serve. Only explicit --serve starts the existing scheduler.");return 0;}
 if(argc>2||(argc==2&&strcmp(argv[1],"--permissions")&&strcmp(argv[1],"--probe-child")&&strcmp(argv[1],"--serve")))return 64;
 NSDictionary *c=settings();if(!c)return 78;
 if(argc==2&&!strcmp(argv[1],"--probe-child"))return probe(c);
 if(argc==2&&!strcmp(argv[1],"--serve"))return serve(c);
 [NSApplication sharedApplication];[NSApp setActivationPolicy:NSApplicationActivationPolicyRegular];[NSApp activateIgnoringOtherApps:YES];
 while(1){NSAlert *a=[NSAlert new];a.messageText=@"车间主任：独立运行授权";a.informativeText=@"请逐项主动授权：辅助功能、屏幕录制、下载文件夹。无需 Apple 账号或完全磁盘访问。授权可能需要关闭重开本应用。当前窗口不会执行任何业务；最后的子 Python 检查才验证实际继承。";
 [a addButtonWithTitle:@"辅助功能"];[a addButtonWithTitle:@"屏幕录制"];[a addButtonWithTitle:@"选择下载文件夹"];[a addButtonWithTitle:@"检查子 Python 权限"];[a addButtonWithTitle:@"关闭"];
 NSModalResponse r=[a runModal];
 if(r==NSAlertFirstButtonReturn){NSDictionary *o=@{(__bridge NSString *)kAXTrustedCheckOptionPrompt:@YES};AXIsProcessTrustedWithOptions((__bridge CFDictionaryRef)o);[[NSWorkspace sharedWorkspace] openURL:[NSURL URLWithString:@"x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"]];}
 else if(r==NSAlertSecondButtonReturn){CGRequestScreenCaptureAccess();[[NSWorkspace sharedWorkspace] openURL:[NSURL URLWithString:@"x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture"]];}
 else if(r==NSAlertThirdButtonReturn)downloads(c);
 else if(r==NSAlertThirdButtonReturn+1){int rc=probe(c);NSAlert *result=[NSAlert new];result.messageText=rc==0?@"子 Python 权限检查通过":@"子 Python 权限未通过，请查看新检查收据";result.informativeText=@"请将独立检查收据交监理核验；本应用不会重试业务或启动服务。";[result runModal];}
 else break;
 }return 0;
}}
