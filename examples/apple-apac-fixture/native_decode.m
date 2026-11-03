#import <Foundation/Foundation.h>
#import <AVFoundation/AVFoundation.h>
#import <CoreMedia/CoreMedia.h>
#include <fcntl.h>
#include <unistd.h>

static void fail(NSString *where, NSError *error) {
    fprintf(stderr,"%s: %s\n",where.UTF8String,error.description.UTF8String ?: "failed");exit(2);
}
// Decode the actual Apple APAC track, selected by its native format description.
// Output is interleaved little-endian signed 16-bit PCM, not a WAV container.
int main(int argc,const char **argv) {
 @autoreleasepool {
    if(argc!=3){fprintf(stderr,"usage: native_decode MIXED_MOV NEW_PCM\n");return 2;}
    AVURLAsset *asset=[AVURLAsset URLAssetWithURL:[NSURL fileURLWithPath:@(argv[1])] options:nil];
    AVAssetTrack *chosen=nil;
    for(AVAssetTrack *track in [asset tracksWithMediaType:AVMediaTypeAudio]) {
        for(id format in track.formatDescriptions) {
            if(CMFormatDescriptionGetMediaSubType((__bridge CMFormatDescriptionRef)format)==kAudioFormatAPAC) {
                if(chosen && chosen!=track)fail(@"ambiguous APAC tracks",nil);chosen=track;
            }
        }
    }
    if(!chosen)fail(@"no genuine Apple APAC format description",nil);
    const AudioStreamBasicDescription *asbd=CMAudioFormatDescriptionGetStreamBasicDescription((__bridge CMAudioFormatDescriptionRef)chosen.formatDescriptions[0]);
    if(!asbd || asbd->mChannelsPerFrame!=2 || asbd->mSampleRate!=48000)fail(@"this fixture check expects stereo 48kHz",nil);
    NSError *error=nil;AVAssetReader *reader=[[AVAssetReader alloc] initWithAsset:asset error:&error];if(!reader)fail(@"reader",error);
    NSDictionary *settings=@{AVFormatIDKey:@(kAudioFormatLinearPCM),AVLinearPCMBitDepthKey:@16,
        AVLinearPCMIsFloatKey:@NO,AVLinearPCMIsBigEndianKey:@NO,AVLinearPCMIsNonInterleaved:@NO};
    AVAssetReaderTrackOutput *output=[[AVAssetReaderTrackOutput alloc] initWithTrack:chosen outputSettings:settings];
    if(![reader canAddOutput:output])fail(@"reader output",reader.error);[reader addOutput:output];
    int fd=open(argv[2],O_WRONLY|O_CREAT|O_EXCL,0600);if(fd<0)fail(@"new PCM output required",nil);
    if(![reader startReading])fail(@"start native decode",reader.error);
    uint64_t total=0,samples=0;CFAbsoluteTime deadline=CFAbsoluteTimeGetCurrent()+25;
    for(;;) {
        if(CFAbsoluteTimeGetCurrent()>deadline)fail(@"native decode timeout",nil);
        CMSampleBufferRef sample=[output copyNextSampleBuffer];
        if(!sample)break;
        CMBlockBufferRef data=CMSampleBufferGetDataBuffer(sample);size_t n=data?CMBlockBufferGetDataLength(data):0;
        if(n>8*1024*1024 || total+n>8*1024*1024)fail(@"PCM size bound",nil);
        NSMutableData *copy=[NSMutableData dataWithLength:n];
        if(!data || CMBlockBufferCopyDataBytes(data,0,n,copy.mutableBytes)!=kCMBlockBufferNoErr)fail(@"PCM buffer",nil);
        size_t offset=0;while(offset<n){ssize_t written=write(fd,(char *)copy.bytes+offset,n-offset);if(written<=0)fail(@"PCM write",nil);offset+=written;}
        total+=n;samples+=CMSampleBufferGetNumSamples(sample);CFRelease(sample);
    }
    close(fd);
    if(reader.status!=AVAssetReaderStatusCompleted || !total)fail(@"native decode incomplete",reader.error);
    printf("{\"native_apac_decoded\":true,\"channels\":2,\"sample_rate\":48000,\"frames\":%llu,\"bytes\":%llu}\n",samples,total);
 }
 return 0;
}
