#import <Foundation/Foundation.h>
#import <AVFoundation/AVFoundation.h>
#import <CoreMedia/CoreMedia.h>
#include <unistd.h>

// Passthrough of original encoded samples, never a fabricated codec tag.
// Arguments: H264_AAC_MOV APPLE_APAC_CAF NEW_MIXED_MOV [apac-first]
static void fail(NSString *where, NSError *error) {
    fprintf(stderr, "%s: %s\n", where.UTF8String, error.description.UTF8String ?: "failed");
    exit(2);
}

int main(int argc, const char **argv) {
 @autoreleasepool {
    if(argc != 4 && argc != 5) { fprintf(stderr,"usage: native_mux VIDEO_AAC_MOV APAC_CAF NEW_OUTPUT_MOV [apac-first]\n"); return 2; }
    BOOL apacFirst=argc==5;
    if(apacFirst && strcmp(argv[4],"apac-first"))fail(@"unknown order option",nil);
    NSURL *videoURL=[NSURL fileURLWithPath:@(argv[1])];
    NSURL *apacURL=[NSURL fileURLWithPath:@(argv[2])];
    NSURL *outURL=[NSURL fileURLWithPath:@(argv[3])];
    if([[NSFileManager defaultManager] fileExistsAtPath:outURL.path])fail(@"existing output refused",nil);
    AVURLAsset *video=[AVURLAsset URLAssetWithURL:videoURL options:nil];
    AVURLAsset *apac=[AVURLAsset URLAssetWithURL:apacURL options:nil];
    NSArray *vt=[video tracksWithMediaType:AVMediaTypeVideo];
    NSArray *at=[video tracksWithMediaType:AVMediaTypeAudio];
    NSArray *pt=[apac tracksWithMediaType:AVMediaTypeAudio];
    if(vt.count != 1 || at.count != 1 || pt.count != 1)fail(@"expected one video, one AAC and one APAC input track",nil);
    NSArray<AVAssetTrack *> *tracks=apacFirst?@[vt[0],pt[0],at[0]]:@[vt[0],at[0],pt[0]];
    NSUInteger apacIndex=apacFirst?1:2;
    FourCharCode types[]={kCMVideoCodecType_H264,apacFirst?kAudioFormatAPAC:kAudioFormatMPEG4AAC,apacFirst?kAudioFormatMPEG4AAC:kAudioFormatAPAC};
    for(NSUInteger i=0;i<tracks.count;i++) {
        NSArray *formats=tracks[i].formatDescriptions;
        if(formats.count!=1 || CMFormatDescriptionGetMediaSubType((__bridge CMFormatDescriptionRef)formats[0])!=types[i])
            fail(@"unexpected genuine source format",nil);
    }
    NSError *error=nil;
    AVAssetReader *vr=[[AVAssetReader alloc] initWithAsset:video error:&error];if(!vr)fail(@"video reader",error);
    AVAssetReader *ar=[[AVAssetReader alloc] initWithAsset:apac error:&error];if(!ar)fail(@"APAC reader",error);
    AVAssetWriter *writer=[[AVAssetWriter alloc] initWithURL:outURL fileType:AVFileTypeQuickTimeMovie error:&error];if(!writer)fail(@"writer",error);
    NSMutableArray<AVAssetReaderTrackOutput *> *outputs=[NSMutableArray array];
    NSMutableArray<AVAssetWriterInput *> *inputs=[NSMutableArray array];
    for(NSUInteger i=0;i<tracks.count;i++) {
        AVAssetTrack *track=tracks[i];
        AVAssetReaderTrackOutput *output=[[AVAssetReaderTrackOutput alloc] initWithTrack:track outputSettings:nil];
        AVAssetReader *reader=i==apacIndex?ar:vr;
        if(![reader canAddOutput:output])fail(@"reader output",reader.error);
        [reader addOutput:output];[outputs addObject:output];
        CMFormatDescriptionRef format=(__bridge CMFormatDescriptionRef)track.formatDescriptions[0];
        AVAssetWriterInput *input=[[AVAssetWriterInput alloc] initWithMediaType:track.mediaType outputSettings:nil sourceFormatHint:format];
        input.expectsMediaDataInRealTime=NO;
        if(i==0)input.transform=track.preferredTransform;
        if(![writer canAddInput:input])fail(@"writer input",writer.error);
        [writer addInput:input];[inputs addObject:input];
    }
    if(![writer startWriting])fail(@"start writing",writer.error);
    [writer startSessionAtSourceTime:kCMTimeZero];
    if(![vr startReading])fail(@"start video reading",vr.error);
    if(![ar startReading])fail(@"start APAC reading",ar.error);
    BOOL done[]={NO,NO,NO}; unsigned counts[]={0,0,0}; NSUInteger complete=0;
    CFAbsoluteTime deadline=CFAbsoluteTimeGetCurrent()+25;
    while(complete<3) {
        if(CFAbsoluteTimeGetCurrent()>deadline) { [writer cancelWriting];fail(@"bounded mux timeout",nil); }
        BOOL progressed=NO;
        for(NSUInteger i=0;i<3;i++) {
            if(done[i] || !inputs[i].readyForMoreMediaData)continue;
            CMSampleBufferRef sample=[outputs[i] copyNextSampleBuffer];
            if(!sample) {
                AVAssetReader *reader=i==apacIndex?ar:vr;
                if(reader.status==AVAssetReaderStatusFailed)fail(@"reading compressed sample",reader.error);
                [inputs[i] markAsFinished];done[i]=YES;complete++;progressed=YES;continue;
            }
            BOOL ok=[inputs[i] appendSampleBuffer:sample];CFRelease(sample);
            if(!ok)fail(@"append compressed sample",writer.error);
            counts[i]++;progressed=YES;
        }
        if(writer.status==AVAssetWriterStatusFailed)fail(@"writer failure",writer.error);
        if(!progressed)usleep(1000);
    }
    dispatch_semaphore_t finished=dispatch_semaphore_create(0);
    [writer finishWritingWithCompletionHandler:^{dispatch_semaphore_signal(finished);}];
    if(dispatch_semaphore_wait(finished,dispatch_time(DISPATCH_TIME_NOW,10*NSEC_PER_SEC)))fail(@"bounded finish timeout",nil);
    if(writer.status!=AVAssetWriterStatusCompleted)fail(@"finish writing",writer.error);
    for(NSUInteger i=0;i<3;i++)if(!counts[i])fail(@"empty source track",nil);
    printf("{\"writer_completed\":true,\"sample_buffers\":[%u,%u,%u]}\n",counts[0],counts[1],counts[2]);
 }
 return 0;
}
