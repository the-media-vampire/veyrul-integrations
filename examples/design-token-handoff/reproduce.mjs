// Run this inspected, read-only fixture from the pinned design-extract root.
// It imports only the two pure formatter modules and prints synthetic output.
import {formatMotionTokens} from './src/formatters/motion-tokens.js';
import {formatDtcgTokens} from './src/formatters/dtcg-tokens.js';
const motion=JSON.parse(formatMotionTokens({
 durations:[{name:'fast',css:'150ms',ms:150}],
 easings:[{family:'ease',raw:'ease'}],
 springs:[{raw:'cubic-bezier(0.34, 1.56, 0.64, 1)'}]
}));
const design=formatDtcgTokens({
 meta:{url:'https://synthetic.invalid/fixture'},
 colors:{primary:'#112233',backgrounds:['#ffffff'],text:['#112233']},
 spacing:{scale:[8]},borders:{radii:[4]},shadows:{values:[]},
 typography:{families:['sans-serif'],body:{size:16,weight:400,lineHeight:1.5}}
});
console.log(JSON.stringify({duration:motion.duration.fast,easing:motion.easing.ease,
 spring:motion.spring['spring-1'],dimension:design.primitive.spacing.s0},null,2));
